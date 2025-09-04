package ca.blackhearttechforge.udp_video_receiver.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import ca.blackhearttechforge.udp_video_receiver.network.UdpReceiver
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.net.InetAddress

data class MainUiState(
    val isScanning: Boolean = false,
    val discoveredDevices: List<InetAddress> = emptyList()
)

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val udpReceiver = UdpReceiver.getInstance(application.applicationContext)
    
    private val _uiState = MutableStateFlow(MainUiState())
    val uiState: StateFlow<MainUiState> = _uiState.asStateFlow()
    
    init {
        viewModelScope.launch {
            udpReceiver.startReceiving()
        }
        
        // Collect discovered devices
        viewModelScope.launch {
            udpReceiver.discoveredDevices.collect { device ->
                val currentDevices = _uiState.value.discoveredDevices
                if (!currentDevices.any { it.hostAddress == device.hostAddress }) {
                    _uiState.value = _uiState.value.copy(
                        discoveredDevices = currentDevices + device
                    )
                }
            }
        }
    }
    
    fun scanForDevices() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isScanning = true,
                discoveredDevices = emptyList()
            )
            
            // Ensure receiver is started and wait for socket to be ready
            udpReceiver.startReceiving()
            
            // Send discovery broadcast
            udpReceiver.discoverDevices()
            
            // Wait for responses (devices have some time to respond)
            delay(3000)
            
            _uiState.value = _uiState.value.copy(isScanning = false)
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        udpReceiver.cleanup()
    }
}
