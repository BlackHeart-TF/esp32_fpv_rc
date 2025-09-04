package ca.blackhearttechforge.udp_video_receiver.ui

import android.graphics.BitmapFactory
import android.view.KeyEvent
import android.view.MotionEvent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlin.math.*

@Composable
fun ViewerScreen(
    cameraIP: String,
    onNavigateBack: () -> Unit,
    viewModel: ViewerViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    LaunchedEffect(cameraIP) {
        viewModel.connectToCamera(cameraIP)
        viewModel.checkGamepadConnection()
    }
    
    DisposableEffect(viewModel) {
        // Register ViewModel for gamepad events
        ca.blackhearttechforge.udp_video_receiver.MainActivity.currentViewerViewModel = viewModel
        
        onDispose {
            // Unregister ViewModel
            ca.blackhearttechforge.udp_video_receiver.MainActivity.currentViewerViewModel = null
            viewModel.disconnect()
        }
    }
    
    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        // Video view - full screen
        uiState.currentFrame?.let { frameData ->
            val bitmap = remember(frameData) {
                BitmapFactory.decodeByteArray(frameData, 0, frameData.size)
            }
            bitmap?.let {
                Image(
                    bitmap = it.asImageBitmap(),
                    contentDescription = "Camera feed",
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Fit // Keep entire video visible
                )
            }
        }
        
        // No video overlay
        if (uiState.currentFrame == null) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black),
                contentAlignment = Alignment.Center
            ) {
                if (uiState.isConnecting) {
                    CircularProgressIndicator(color = Color.White)
                } else if (uiState.errorMessage != null) {
                    Text(
                        text = uiState.errorMessage ?: "Unknown error",
                        color = Color.Red
                    )
                } else {
                    Text(
                        text = "No video signal",
                        color = Color.White
                    )
                }
            }
        }
        
        // Floating back button - top left
        FloatingActionButton(
            onClick = onNavigateBack,
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(16.dp)
                .size(48.dp),
            containerColor = Color.Black.copy(alpha = 0.5f),
            contentColor = Color.White
        ) {
            Icon(
                Icons.Default.ArrowBack, 
                contentDescription = "Back",
                tint = Color.White
            )
        }
        
        // Gamepad status indicator - top right
        if (uiState.gamepadConnected) {
            Card(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color.Green.copy(alpha = 0.8f))
            ) {
                Text(
                    text = "🎮 ${uiState.gamepadName?.take(10) ?: "Gamepad"}",
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                    color = Color.White,
                    fontSize = 12.sp
                )
            }
        }
        
        // Virtual joystick overlay - bottom right
        VirtualJoystick(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(16.dp)
                .size(120.dp),
            onPositionChange = { x, y ->
                viewModel.updateJoystickPosition(x, y)
            }
        )
    }
}

@Composable
fun VirtualJoystick(
    modifier: Modifier = Modifier,
    onPositionChange: (x: Float, y: Float) -> Unit
) {
    var center by remember { mutableStateOf(Offset.Zero) }
    var knobPosition by remember { mutableStateOf(Offset.Zero) }
    val density = LocalDensity.current
    
    val joystickRadius = with(density) { 60.dp.toPx() }
    val knobRadius = with(density) { 20.dp.toPx() }
    
    Canvas(
        modifier = modifier
            .clip(CircleShape)
            .background(Color.Black.copy(alpha = 0.3f))
            .pointerInput(Unit) {
                detectDragGestures(
                    onDragStart = { offset ->
                        center = Offset(size.width / 2f, size.height / 2f)
                        knobPosition = offset
                    },
                    onDragEnd = {
                        knobPosition = center
                        onPositionChange(0f, 0f)
                    },
                    onDrag = { _, dragAmount ->
                        val newPosition = knobPosition + dragAmount
                        val distance = (newPosition - center).getDistance()
                        
                        knobPosition = if (distance <= joystickRadius - knobRadius) {
                            newPosition
                        } else {
                            val angle = atan2(newPosition.y - center.y, newPosition.x - center.x)
                            val maxDistance = joystickRadius - knobRadius
                            center + Offset(
                                cos(angle) * maxDistance,
                                sin(angle) * maxDistance
                            )
                        }
                        
                        // Convert to normalized coordinates (-1 to 1)
                        val normalizedX = (knobPosition.x - center.x) / (joystickRadius - knobRadius)
                        val normalizedY = (knobPosition.y - center.y) / (joystickRadius - knobRadius)
                        onPositionChange(normalizedX, normalizedY)
                    }
                )
            }
    ) {
        val canvasCenter = Offset(size.width / 2f, size.height / 2f)
        center = canvasCenter
        if (knobPosition == Offset.Zero) {
            knobPosition = canvasCenter
        }
        
        // Draw outer circle
        drawCircle(
            color = Color.White.copy(alpha = 0.3f),
            radius = joystickRadius,
            center = canvasCenter
        )
        
        // Draw knob
        drawCircle(
            color = Color.White.copy(alpha = 0.8f),
            radius = knobRadius,
            center = knobPosition
        )
    }
}
