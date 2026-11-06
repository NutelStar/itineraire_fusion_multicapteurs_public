import argparse
import cv2
import mediapipe as mp

from sensors.CAMERA import Camera
from core.calibration import load_calibration, undistort_image
from config import  DISPLAY_SIZE
from core.display import show_frame

DEBUG_TEXT = True

LEFT_EYE = [33, 133]
RIGHT_EYE = [362, 263]

MOUTH = [13, 14]

LEFT_EYEBROW = [70, 105]
RIGHT_EYEBROW = [336, 300]

def initialize_camera():
    print("Initialisation de la caméra...")

    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    return camera

def initialize_face_mesh():
    mp_face_mesh = mp.solutions.face_mesh

    return mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

def draw_points(frame, face_landmarks, indices, color, label, text = DEBUG_TEXT):
    """
    Dessine les points du module mediapipe sur la frame.
    """

    h, w, _ = frame.shape

    for i in indices:
        lm = face_landmarks.landmark[i]

        x = int(lm.x * w)
        y = int(lm.y * h)

        cv2.circle(frame, (x, y), 5, color, -1)

        # Ajoute du texte pour le debug
        if text:
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


def draw_face_landmarks(frame, face_landmarks):
    """
    Dessine les points particuliers correspondant aux indices des yeux, de la bouche etc.
    """
    h, w, _ = frame.shape

    # Tous les points
    for idx, landmark in enumerate(face_landmarks.landmark):
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

    # Ajoute de la couleur et du texte sur des points spéciaux du visage
    draw_points(frame, face_landmarks, LEFT_EYE, (255, 0, 0), "Eye")
    draw_points(frame, face_landmarks, RIGHT_EYE, (255, 0, 0), "Eye")

    draw_points(frame, face_landmarks, MOUTH, (0, 0, 255), "Mouth")

    draw_points(frame, face_landmarks, LEFT_EYEBROW, (0, 255, 255), "Brow")
    draw_points(frame, face_landmarks, RIGHT_EYEBROW, (0, 255, 255), "Brow")

def detection_du_visage(camera, calibration, face_mesh, size=None):

    print("Affichage du flux avec détection du visage.")
    print("Appuyer sur 'q' pour quitter.")

    while True:

        # Capture la frame
        frame = camera.capture_frame()

        # Correction de la distorsion
        frame = undistort_image(frame, calibration, crop=False)

        # Flip horizontal de la frame
        frame = cv2.flip(frame, 1)

        # Conversion en RGB (la frame est en BGR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Détection du visage
        results = face_mesh.process(rgb_frame)

        # multi_face_landmarks contient les informations de PLUSIEURS visages sur la frame
        if results.multi_face_landmarks:

            # Récupère chaque ensemble de points pour chaque visage
            for face_landmarks in results.multi_face_landmarks:
                draw_face_landmarks(frame, face_landmarks)

        if show_frame(
            frame,
            "Face detection",
            exit_key="q",
            size=size
        ):
            break


def main(calibration_file, size=None):

    # Initialisation
    camera = initialize_camera()
    calibration = load_calibration(calibration_file)
    face_mesh = initialize_face_mesh()

    try:
        detection_du_visage(
            camera=camera,
            calibration=calibration,
            face_mesh=face_mesh,
            size=size
        )
    finally:
        cv2.destroyAllWindows()
        camera.stop()
        print("Ressources libérées.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Détection du visage avec le module mediapipe."
    )

    parser.add_argument(
        "calibration_file",
        type=str,
        help="Fichier de calibration."
    )

    parser.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        help="Taille de la fenêtre."
    )

    args = parser.parse_args()

    display_size = (
        tuple(args.size)
        if args.size is not None
        else DISPLAY_SIZE
    )

    main(
        calibration_file=args.calibration_file,
        size=display_size
    )