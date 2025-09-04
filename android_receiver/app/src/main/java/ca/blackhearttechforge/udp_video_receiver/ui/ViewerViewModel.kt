package ca.blackhearttechforge.udp_video_receiver.ui

import android.app.Application
import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import ca.blackhearttechforge.udp_video_receiver.network.UdpReceiver
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.net.InetAddress

data class ViewerUiState(
    val isConnecting: Boolean = false,
    val isConnected: Boolean = false,
    val currentFrame: ByteArray? = null,
    val joystickX: Float = 0f,
    val joystickY: Float = 0f,
    val errorMessage: String? = null,
    val gamepadConnected: Boolean = false,
    val gamepadName: String? = null
)

class ViewerViewModel(application: Application) : AndroidViewModel(application) {
    private val udpReceiver = UdpReceiver.getInstance(application.applicationContext)
    
    private val _uiState = MutableStateFlow(ViewerUiState())
    val uiState: StateFlow<ViewerUiState> = _uiState.asStateFlow()
    
    private var currentTarget: InetAddress? = null
    private var servoUpdateJob: Job? = null
    private var lastGamepadX: Float = 0f
    private var lastGamepadY: Float = 0f
    private var gamepadCheckJob: Job? = null
    private var lastGamepadEventTime: Long = 0L
    
    init {
        viewModelScope.launch {
            udpReceiver.startReceiving()
        }
        
        // Collect frames
        viewModelScope.launch {
            udpReceiver.frameFlow.collect { frame ->
                _uiState.value = _uiState.value.copy(
                    currentFrame = frame,
                    isConnected = true,
                    isConnecting = false
                )
            }
        }
    }
    
    fun connectToCamera(ipAddress: String) {
        viewModelScope.launch {
            try {
                println("Connecting to camera: $ipAddress")
                _uiState.value = _uiState.value.copy(isConnecting = true)
                
                val target = InetAddress.getByName(ipAddress)
                currentTarget = target
                println("Target resolved: ${target.hostAddress}")
                
                udpReceiver.startStream(target)
                println("Stream started")
                
                startServoUpdates(target)
                startGamepadMonitoring()
                println("Servo updates and gamepad monitoring started")
                
            } catch (e: Exception) {
                println("Connection error: ${e.message}")
                _uiState.value = _uiState.value.copy(
                    isConnecting = false,
                    isConnected = false,
                    errorMessage = "Connection failed: ${e.message}"
                )
                e.printStackTrace()
            }
        }
    }
    
    fun updateJoystickPosition(x: Float, y: Float) {
        _uiState.value = _uiState.value.copy(
            joystickX = x,
            joystickY = y
        )
    }
    
    private fun startServoUpdates(target: InetAddress) {
        servoUpdateJob?.cancel()
        servoUpdateJob = viewModelScope.launch {
            while (isActive) {
                val state = _uiState.value
                
                // Convert joystick position (-1 to 1) to servo values (1000 to 2000)
                val servoX = ((state.joystickX + 1f) * 500f + 1000f).toInt().coerceIn(1000, 2000)
                val servoY = ((state.joystickY + 1f) * 500f + 1000f).toInt().coerceIn(1000, 2000)
                
                udpReceiver.sendServoCommand(target, servoX, servoY)
                
                delay(20) // Send updates every 20ms
            }
        }
    }
    
    fun disconnect() {
        servoUpdateJob?.cancel()
        gamepadCheckJob?.cancel()
        currentTarget?.let { target ->
            viewModelScope.launch {
                udpReceiver.stopStream(target)
            }
        }
        _uiState.value = ViewerUiState()
    }
    
    override fun onCleared() {
        super.onCleared()
        disconnect()
        udpReceiver.cleanup()
    }
    
    // Gamepad handling
    fun onGamepadMotionEvent(event: MotionEvent): Boolean {
        if (event.source and InputDevice.SOURCE_JOYSTICK != InputDevice.SOURCE_JOYSTICK) {
            return false
        }
        
        // Update last gamepad event timestamp
        lastGamepadEventTime = System.currentTimeMillis()
        
        // Get left stick X and Y axes (usually AXIS_X and AXIS_Y)
        val x = event.getAxisValue(MotionEvent.AXIS_X)
        val y = -event.getAxisValue(MotionEvent.AXIS_Y) // Invert Y axis
        
        // Only update if values actually changed (avoid spam)
        if (x != lastGamepadX || y != lastGamepadY) {
            lastGamepadX = x
            lastGamepadY = y
            
            // Update joystick position in UI state
            updateJoystickPosition(x, y)
            
            // Update gamepad connection status
            val device = InputDevice.getDevice(event.deviceId)
            _uiState.value = _uiState.value.copy(
                gamepadConnected = true,
                gamepadName = device?.name
            )
        }
        
        return true
    }
    
    fun onGamepadKeyEvent(event: KeyEvent): Boolean {
        if (event.source and InputDevice.SOURCE_GAMEPAD != InputDevice.SOURCE_GAMEPAD) {
            return false
        }
        
        // Handle gamepad buttons here if needed (e.g., start/stop stream)
        return when (event.keyCode) {
            KeyEvent.KEYCODE_BUTTON_START -> {
                // Could trigger stream start/stop
                true
            }
            else -> false
        }
    }
    
    fun checkGamepadConnection() {
        // Check for connected gamepads
        val inputDeviceIds = InputDevice.getDeviceIds()
        var gamepadFound = false
        var gamepadName: String? = null
        
        for (deviceId in inputDeviceIds) {
            val device = InputDevice.getDevice(deviceId)
            if (device != null && 
                (device.sources and InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK) {
                gamepadFound = true
                gamepadName = device.name
                break
            }
        }
        
        _uiState.value = _uiState.value.copy(
            gamepadConnected = gamepadFound,
            gamepadName = gamepadName
        )
    }
    
    private fun startGamepadMonitoring() {
        gamepadCheckJob = viewModelScope.launch {
            while (isActive) {
                delay(1000) // Check every 1 second
                
                // Only check if gamepad is still physically connected
                // Don't timeout based on events - let hardware disconnection handle it
                val wasConnected = _uiState.value.gamepadConnected
                checkGamepadConnection()
                
                // If gamepad was connected but now physically disconnected, send neutral
                if (wasConnected && !_uiState.value.gamepadConnected) {
                    updateJoystickPosition(0f, 0f)
                    lastGamepadX = 0f
                    lastGamepadY = 0f
                }
            }
        }
    }
}
