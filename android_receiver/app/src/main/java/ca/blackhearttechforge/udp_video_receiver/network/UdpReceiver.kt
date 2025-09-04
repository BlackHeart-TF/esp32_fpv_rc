package ca.blackhearttechforge.udp_video_receiver.network

import android.content.Context
import android.net.wifi.WifiManager
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import java.net.*
import java.nio.ByteBuffer
import java.nio.ByteOrder

class UdpReceiver private constructor(private val context: Context) {
    companion object {
        @Volatile
        private var INSTANCE: UdpReceiver? = null
        
        fun getInstance(context: Context): UdpReceiver {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: UdpReceiver(context.applicationContext).also { INSTANCE = it }
            }
        }
        
        // Constants
        const val LISTEN_PORT = 55556
        const val TARGET_PORT = 55555
        const val CMD_DISCOVER = 0x55.toByte()
        const val CMD_STOP_STREAM = 0x56.toByte()
        const val CMD_START_STREAM = 0x57.toByte()
        const val CMD_SERVO = 0x54.toByte()
        
        private val SOI = byteArrayOf(0xFF.toByte(), 0xD8.toByte(), 0xFF.toByte())
        private val EOI = byteArrayOf(0xFF.toByte(), 0xD9.toByte())
    }
    
    private val _frameFlow = MutableSharedFlow<ByteArray>(
        replay = 0,
        extraBufferCapacity = 1  // Minimal buffer for low latency
    )
    val frameFlow: SharedFlow<ByteArray> = _frameFlow.asSharedFlow()
    
    private val _discoveredDevices = MutableSharedFlow<InetAddress>()
    val discoveredDevices: SharedFlow<InetAddress> = _discoveredDevices.asSharedFlow()
    
    private var receiveJob: Job? = null
    private var socket: DatagramSocket? = null
    private var multicastLock: WifiManager.MulticastLock? = null
    
    suspend fun startReceiving() {
        if (receiveJob?.isActive == true) return
        
        // Use a CompletableDeferred to wait until socket is ready
        val socketReady = CompletableDeferred<Unit>()
        
        receiveJob = CoroutineScope(Dispatchers.IO).launch {
            try {
                // Acquire multicast lock - this is Android's way to "allow UDP through firewall"
                val wifiManager = context.getSystemService(Context.WIFI_SERVICE) as WifiManager
                multicastLock = wifiManager.createMulticastLock("UdpReceiver").apply {
                    setReferenceCounted(false)
                    acquire()
                }
                // Explicitly bind to IPv4 to avoid IPv6-only binding  
                val ipv4SocketAddress = InetSocketAddress("0.0.0.0", LISTEN_PORT)
                socket = DatagramSocket(ipv4SocketAddress).apply { 
                    reuseAddress = true
                    broadcast = true  // Enable broadcast for sending
                }
                
                // Signal that socket is ready
                socketReady.complete(Unit)
                
                val buffer = ByteArray(65536)
                var chunks = ByteArray(0)
                while (isActive) {
                    val packet = DatagramPacket(buffer, buffer.size)
                    try {
                        socket?.receive(packet)
                        
                        val dataSize = packet.length
                        val sourceIP = packet.address
                        
                        // Handle discovery responses (single byte responses to discovery broadcast)
                        if (dataSize == 1 && buffer[0] == CMD_DISCOVER) {
                            _discoveredDevices.emit(sourceIP)
                            continue
                        }
                        
                        // Handle JPEG frame data - work directly with buffer to avoid copying
                        val data = buffer.sliceArray(0 until dataSize)
                        val soiIndex = data.indexOfSubArray(SOI)
                        val eoiIndex = data.lastIndexOfSubArray(EOI)
                        
                        if (soiIndex >= 0) {
                            // New frame starts - emit any complete previous frame
                            if (chunks.startsWithSOI() && eoiIndex >= 0) {
                                val completeFrame = chunks + data.sliceArray(0 until eoiIndex + 2)
                                _frameFlow.emit(completeFrame)
                            }
                            chunks = data.sliceArray(soiIndex until dataSize)
                        } else {
                            chunks += data
                        }
                        
                        if (eoiIndex >= 0 && chunks.startsWithSOI()) {
                            val endIndex = chunks.size - dataSize + eoiIndex + 2
                            val completeFrame = chunks.sliceArray(0 until endIndex)
                            _frameFlow.emit(completeFrame)
                            chunks = chunks.sliceArray(endIndex until chunks.size)
                        }
                    } catch (e: Exception) {
                        // Don't break the loop on receive errors - just continue
                    }
                }
            } catch (e: Exception) {
                println("Socket error: ${e.message}")
                socketReady.completeExceptionally(e)
                e.printStackTrace()
            }
        }
        
        // Wait for socket to be ready before returning
        socketReady.await()
    }
    
    fun stopReceiving() {
        receiveJob?.cancel()
        socket?.close()
        socket = null
        multicastLock?.release()
        multicastLock = null
    }
    
    suspend fun discoverDevices() = withContext(Dispatchers.IO) {
        try {
            socket?.let { sock ->
                val broadcastAddress = InetAddress.getByName("255.255.255.255")
                val packet = DatagramPacket(
                    byteArrayOf(CMD_DISCOVER),
                    1,
                    broadcastAddress,
                    TARGET_PORT
                )
                println("Sending discovery broadcast to 255.255.255.255:$TARGET_PORT from port ${sock.localPort}")
                sock.send(packet)
            } ?: run {
                println("Socket not initialized for discovery!")
            }
        } catch (e: Exception) {
            println("Discovery error: ${e.message}")
            e.printStackTrace()
        }
    }
    
    suspend fun startStream(targetIP: InetAddress) = withContext(Dispatchers.IO) {
        try {
            socket?.let { sock ->
                sock.send(DatagramPacket(byteArrayOf(CMD_DISCOVER), 1, targetIP, TARGET_PORT))
                sock.send(DatagramPacket(byteArrayOf(CMD_START_STREAM), 1, targetIP, TARGET_PORT))
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    suspend fun stopStream(targetIP: InetAddress) = withContext(Dispatchers.IO) {
        try {
            socket?.send(
                DatagramPacket(byteArrayOf(CMD_STOP_STREAM), 1, targetIP, TARGET_PORT)
            )
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    suspend fun sendServoCommand(targetIP: InetAddress, x: Int, y: Int) = withContext(Dispatchers.IO) {
        try {
            val buffer = ByteBuffer.allocate(5).order(ByteOrder.LITTLE_ENDIAN)
            buffer.put(CMD_SERVO)
            buffer.putShort(x.coerceIn(1000, 2000).toShort())
            buffer.putShort(y.coerceIn(1000, 2000).toShort())
            
            socket?.send(
                DatagramPacket(buffer.array(), buffer.capacity(), targetIP, TARGET_PORT)
            )
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    fun cleanup() {
        stopReceiving()
    }
}

// Extension functions for byte array operations
private fun ByteArray.indexOfSubArray(subArray: ByteArray): Int {
    for (i in 0..this.size - subArray.size) {
        var found = true
        for (j in subArray.indices) {
            if (this[i + j] != subArray[j]) {
                found = false
                break
            }
        }
        if (found) return i
    }
    return -1
}

private fun ByteArray.lastIndexOfSubArray(subArray: ByteArray): Int {
    for (i in this.size - subArray.size downTo 0) {
        var found = true
        for (j in subArray.indices) {
            if (this[i + j] != subArray[j]) {
                found = false
                break
            }
        }
        if (found) return i
    }
    return -1
}

private fun ByteArray.startsWithSOI(): Boolean {
    return this.size >= 3 && 
           this[0] == 0xFF.toByte() && 
           this[1] == 0xD8.toByte() && 
           this[2] == 0xFF.toByte()
}
