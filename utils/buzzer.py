
from config import PORT_BUZZER
import RPi.GPIO as GPIO
import time


class buzzer:
    """
    Classe pour l'utilisation d'un buzzer.

    Utilisation simple :
    
        buzzer_obj = buzzer(27)
        buzzer_obj.beep(0.5)  # Bip de 0.5 secondes
        buzzer_obj.on()       # Buzzer activé
        time.sleep(1)
        buzzer_obj.off()      # Buzzer désactivé
        buzzer_obj.cleanup()
    Branchement
    -----------
    + : VCC (3.3V ou 5V)
    - : GND
    S : PORT GPIO
    """

    def __init__(self):
        """
        Initialise le buzzer sur le port GPIO défini en config.
        """
        self.pin = PORT_BUZZER
        self._cleaned = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        """
        Active le buzzer (bruit continu).
        """
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        """
        Désactive le buzzer.
        """
        GPIO.output(self.pin, GPIO.LOW)

    def beep(self, duration=0.1, nb_beeps=1, interval=0.1):
        """
        Produit un ou plusieurs bips.

        Parameters
        ----------
        duration : float
            Durée de chaque bip en secondes.
        nb_beeps : int
            Nombre de bips à produire.
        interval : float
            Intervalle entre les bips en secondes.
        """
        for _ in range(nb_beeps):
            self.on()
            time.sleep(duration)
            self.off()
            if _ < nb_beeps - 1:
                time.sleep(interval)

    def cleanup(self):
        """
        Libère les ressources GPIO associées au buzzer.
        """
        if not self._cleaned:
            self.off()
            GPIO.cleanup(self.pin)
            self._cleaned = True
