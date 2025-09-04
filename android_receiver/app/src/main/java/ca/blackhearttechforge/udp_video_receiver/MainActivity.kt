package ca.blackhearttechforge.udp_video_receiver

import android.os.Bundle
import android.view.KeyEvent
import android.view.MotionEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import ca.blackhearttechforge.udp_video_receiver.ui.MainScreen
import ca.blackhearttechforge.udp_video_receiver.ui.ViewerScreen
import ca.blackhearttechforge.udp_video_receiver.ui.theme.ESP32FPVRCTheme

class MainActivity : ComponentActivity() {
    companion object {
        var currentViewerViewModel: ca.blackhearttechforge.udp_video_receiver.ui.ViewerViewModel? = null
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ESP32FPVRCTheme {
                ESP32FPVRCApp()
            }
        }
    }
    
    override fun onGenericMotionEvent(event: MotionEvent?): Boolean {
        return if (event != null && currentViewerViewModel?.onGamepadMotionEvent(event) == true) {
            true
        } else {
            super.onGenericMotionEvent(event)
        }
    }
    
    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        return if (event != null && currentViewerViewModel?.onGamepadKeyEvent(event) == true) {
            true
        } else {
            super.onKeyDown(keyCode, event)
        }
    }
}

@Composable
fun ESP32FPVRCApp() {
    val navController = rememberNavController()
    
    Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
        ESP32FPVRCNavHost(
            navController = navController,
            modifier = Modifier.padding(innerPadding)
        )
    }
}

@Composable
fun ESP32FPVRCNavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = "main",
        modifier = modifier
    ) {
        composable("main") {
            MainScreen(
                onNavigateToViewer = { cameraIP ->
                    navController.navigate("viewer/$cameraIP")
                }
            )
        }
        
        composable("viewer/{cameraIP}") { backStackEntry ->
            val cameraIP = backStackEntry.arguments?.getString("cameraIP") ?: ""
            ViewerScreen(
                cameraIP = cameraIP,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}