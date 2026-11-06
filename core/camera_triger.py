from sensors.CAMERA.camera import Camera
import config.parameters as params

class CameraTrigger:
    def __init__(self):
        self.cam_sensor = None
        self.active = False
        self.resolution = None
        self.fps = None

    def init_camera(self, resolution=None, fps=None):
        """
        Initialise la caméra. 
        Si resolution ou fps ne sont pas fournis, on prend ceux de parameters.py
        """
        # Récupération des paramètres par défaut si non fournis
        if resolution is None:
            resolution = params.CAMERA_RESOLUTION
        if fps is None:
            fps = params.CAMERA_FRAMERATE

        self.resolution = resolution
        self.fps = fps
        
        # Instanciation et configuration de la caméra bas niveau (Picamera2)
        self.cam_sensor = Camera()
        self.cam_sensor.configure(resolution=self.resolution, framerate=self.fps)

    def start_camera(self):
        """Démarre le flux de la caméra."""
        if self.cam_sensor is not None:
            self.cam_sensor.start()
            # On utilise le warmup défini dans le capteur pour stabiliser l'image
            self.cam_sensor.warmup() 
            self.active = True

    def stop_camera(self):
        """Arrête la caméra et libère les ressources."""
        if self.cam_sensor is not None:
            self.cam_sensor.stop()
        self.active = False

    def capture_frame(self):
        """
        Capture une frame si la caméra est active.
        Retourne la frame ou None si échec.
        """
        if not self.active or self.cam_sensor is None:
            return None
        
        try:
            frame = self.cam_sensor.capture_frame()
            return frame
        except Exception as e:
            print(f"Erreur lors de la capture : {e}")
            return None

    def is_camera_active(self):
        """Retourne l'état actuel de la caméra."""
        if self.cam_sensor is not None:
            return self.cam_sensor.is_running
        return False