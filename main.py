import threading
import time
import cv2
import customtkinter as ctk
import numpy as np
import pyautogui
from PIL import ImageGrab
from ultralytics import YOLO

# Arayüz Teması
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class FishingBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SonOyuncu Balık Tutma Botu (YOLOv8)")
        self.geometry("450x400")
        self.resizable(False, False)

        # Bot Değişkenleri
        self.is_running = False
        self.model = None
        self.bot_thread = None
        
        # Ayarlanabilir Parametreler
        self.confidence_level = 0.50
        self.click_delay = 1.0

        # Arayüz Elemanları
        self.setup_ui()

    def setup_ui(self):
        # Başlık
        self.title_label = ctk.CTkLabel(self, text="Minecraft Otomatik Balık Botu", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        # Güven Oranı (Confidence) Ayarı
        self.conf_label = ctk.CTkLabel(self, text=f"YOLO Güven Oranı: %{int(self.confidence_level*100)}")
        self.conf_label.pack(pady=5)
        self.conf_slider = ctk.CTkSlider(self, from_=0.1, to=0.9, command=self.update_conf)
        self.conf_slider.set(self.confidence_level)
        self.conf_slider.pack(pady=5)

        # Tıklama Gecikmesi Ayarı
        self.delay_label = ctk.CTkLabel(self, text=f"Tıklama Gecikmesi: {self.click_delay} sn")
        self.delay_label.pack(pady=5)
        self.delay_slider = ctk.CTkSlider(self, from_=0.5, to=3.0, command=self.update_delay)
        self.delay_slider.set(self.click_delay)
        self.delay_slider.pack(pady=5)

        # Durum Yazısı
        self.status_label = ctk.CTkLabel(self, text="Durum: Model Yüklenmedi", text_color="yellow")
        self.status_label.pack(pady=15)

        # Başlat / Durdur Butonları
        self.start_button = ctk.CTkButton(self, text="Botu Başlat", command=self.start_bot, state="disabled")
        self.start_button.pack(pady=10)

        self.stop_button = ctk.CTkButton(self, text="Botu Durdur", command=self.stop_bot, fg_color="red", state="disabled")
        self.stop_button.pack(pady=5)

        # Modeli Arka Planda Yükle
        threading.Thread(target=self.load_model, daemon=True).start()

    def load_model(self):
        try:
            # Aynı klasördeki best.pt dosyasını okur
            self.model = YOLO("best.pt")
            self.status_label.configure(text="Durum: Model Hazır, Bot Beklemede", text_color="green")
            self.start_button.configure(state="normal")
        except Exception as e:
            self.status_label.configure(text="Hata: 'best.pt' bulunamadı!", text_color="red")

    def update_conf(self, value):
        self.confidence_level = value
        self.conf_label.configure(text=f"YOLO Güven Oranı: %{int(self.confidence_level*100)}")

    def update_delay(self, value):
        self.click_delay = round(value, 1)
        self.delay_label.configure(text=f"Tıklama Gecikmesi: {self.click_delay} sn")

    def start_bot(self):
        if not self.is_running:
            self.is_running = True
            self.status_label.configure(text="Durum: Bot Aktif! İzleniyor...", text_color="cyan")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            
            # Botu ana arayüzü dondurmaması için ayrı thread'de başlatıyoruz
            self.bot_thread = threading.Thread(target=self.fishing_loop, daemon=True)
            self.bot_thread.start()

    def stop_bot(self):
        if self.is_running:
            self.is_running = False
            self.status_label.configure(text="Durum: Bot Durduruldu.", text_color="orange")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def fishing_loop(self):
        while self.is_running:
            # Tüm ekranın görüntüsünü yakala
            screen = np.array(ImageGrab.grab())
            screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

            # YOLO ile ekrandaki 'rod' (olta mantarı) nesnesini ara
            results = self.model(screen_bgr, conf=self.confidence_level, verbose=False)
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Olta mantarının koordinatlarını al
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Olta mantarının etrafında partikül aramak için küçük bir alan (ROI) kes
                    # Mantarın biraz altını ve çevresini tarıyoruz (Su sıçrama alanı)
                    padding = 40
                    h, w, _ = screen_bgr.shape
                    roi_y1 = max(0, y1 - padding)
                    roi_y2 = min(h, y2 + padding)
                    roi_x1 = max(0, x1 - padding)
                    roi_x2 = min(w, x2 + padding)
                    
                    roi = screen_bgr[roi_y1:roi_y2, roi_x1:roi_x2]
                    
                    # Minecraft su partikülleri için renk filtresi (Beyaz/Açık Mavi pikseller)
                    # Dokunuşa duyarlılığı artırmak için HSV renk uzayı kullanılabilir
                    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                    lower_particle = np.array([0, 0, 200])   # Parlak beyazımsı pikseller
                    upper_particle = np.array([180, 50, 255])
                    mask = cv2.inRange(hsv, lower_particle, upper_particle)
                    
                    # Eğer maskelenen alanda yeterli miktarda partikül pikseli varsa (Balık vurduysa)
                    particle_count = np.sum(mask == 255)
                    if particle_count > 15:  # Bu eşik değeri partikül yoğunluğuna göre ayarlanabilir
                        print("[BOT] Balık yakalandı! Olta çekiliyor...")
                        
                        # 1. Sağ Tık: Oltayı Çek
                        pyautogui.rightClick()
                        time.sleep(self.click_delay)
                        
                        # 2. Sağ Tık: Oltayı Tekrar At
                        pyautogui.rightClick()
                        
                        # Ardışık tıklamaları önlemek için güvenli bekleme süresi
                        time.sleep(3.0) 
                        break
            
            time.sleep(0.1) # İşlemciyi yormamak için kısa bekleme

if __name__ == "__main__":
    app = FishingBotApp()
    app.mainloop()
  
