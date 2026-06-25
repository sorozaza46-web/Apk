import os
import sys

# OpenCV'nin Windows medya kitaplıklarıyla döngüye girip çökmesini engeller
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

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

        self.title("SonOyuncu Balık Tutma Botu v4 (Hibrit Sistem)")
        self.geometry("500x550")
        self.resizable(False, False)

        # Bot Değişkenleri
        self.is_running = False
        self.model = None
        self.mantar_template = None
        self.bot_thread = None
        
        # Ayarlanabilir Parametreler
        self.confidence_level = 0.30  
        self.click_delay = 1.0

        self.setup_ui()

    def setup_ui(self):
        # Başlık
        self.title_label = ctk.CTkLabel(self, text="Minecraft Hibrit Balık Botu", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=15)

        # Güven Oranı (Confidence) Ayarı
        self.conf_label = ctk.CTkLabel(self, text=f"YOLO Güven Oranı: %{int(self.confidence_level*100)}")
        self.conf_label.pack(pady=2)
        self.conf_slider = ctk.CTkSlider(self, from_=0.1, to=0.9, command=self.update_conf)
        self.conf_slider.set(self.confidence_level)
        self.conf_slider.pack(pady=5)

        # Tıklama Gecikmesi Ayarı
        self.delay_label = ctk.CTkLabel(self, text=f"Tıklama Gecikmesi: {self.click_delay} sn")
        self.delay_label.pack(pady=2)
        self.delay_slider = ctk.CTkSlider(self, from_=0.5, to=3.0, command=self.update_delay)
        self.delay_slider.set(self.click_delay)
        self.delay_slider.pack(pady=5)

        # Durum Yazısı
        self.status_label = ctk.CTkLabel(self, text="Durum: Kaynaklar Yüklenmedi", text_color="yellow", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=10)

        # CANLI GERİ BİLDİRİM ALANI (KONSOL)
        self.console_label = ctk.CTkLabel(self, text="Canlı Geri Bildirim:", font=ctk.CTkFont(size=12, weight="bold"))
        self.console_label.pack(pady=2)
        
        self.textbox = ctk.CTkTextbox(self, width=420, height=140, activate_scrollbars=True)
        self.textbox.pack(pady=5)
        self.log_message("Sistem başlatıldı. Model ve mantar.png yükleniyor...")

        # Başlat / Durdur Butonları
        self.start_button = ctk.CTkButton(self, text="Botu Başlat", command=self.start_bot, state="disabled")
        self.start_button.pack(pady=8)

        self.stop_button = ctk.CTkButton(self, text="Botu Durdur", command=self.stop_bot, fg_color="red", state="disabled")
        self.stop_button.pack(pady=3)

        # Kaynakları Arka Planda Yükle
        threading.Thread(target=self.load_resources, daemon=True).start()

    def log_message(self, message):
        current_time = time.strftime("%H:%M:%S")
        self.textbox.insert("end", f"[{current_time}] {message}\n")
        self.textbox.see("end")

    def load_resources(self):
        # 1. YOLO Modelini Yükle
        try:
            if hasattr(sys, '_MEIPASS'):
                model_path = os.path.join(sys._MEIPASS, "best.pt")
                template_path = os.path.join(sys._MEIPASS, "mantar.png")
            else:
                model_path = "best.pt"
                template_path = "mantar.png"

            self.model = YOLO(model_path)
            self.log_message("YOLOv8 (best.pt) başarıyla yüklendi.")
            
            # 2. Şablon Mantar Görselini Yükle
            if os.path.exists(template_path):
                self.mantar_template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                self.log_message("Görsel referansı (mantar.png) başarıyla yüklendi.")
                self.status_label.configure(text="Durum: Hibrit Sistem Hazır", text_color="green")
                self.start_button.configure(state="normal")
            else:
                self.status_label.configure(text="Hata: 'mantar.png' eksik!", text_color="red")
                self.log_message("HATA: Klasörde 'mantar.png' bulunamadı! Lütfen ekleyin.")
        except Exception as e:
            self.status_label.configure(text="Hata: Yükleme başarısız!", text_color="red")
            self.log_message(f"HATA: {str(e)}")

    def update_conf(self, value):
        self.confidence_level = value
        self.conf_label.configure(text=f"YOLO Güven Oranı: %{int(self.confidence_level*100)}")

    def update_delay(self, value):
        self.click_delay = round(value, 1)
        self.delay_label.configure(text=f"Tıklama Gecikmesi: {self.click_delay} sn")

    def start_bot(self):
        if not self.is_running:
            self.is_running = True
            self.status_label.configure(text="Durum: Bot Aktif!", text_color="cyan")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            
            self.bot_thread = threading.Thread(target=self.fishing_loop, daemon=True)
            self.bot_thread.start()

    def stop_bot(self):
        if self.is_running:
            self.is_running = False
            self.status_label.configure(text="Durum: Bot Durduruldu.", text_color="orange")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.log_message("Bot kullanıcı tarafından durduruldu.")

    def fishing_loop(self):
        self.log_message("Oyuna geçmeniz için 2 saniye bekleniyor...")
        time.sleep(2.0)
        if not self.is_running: return
        
        self.log_message("İlk olta fırlatılıyor... (Sağ Tık)")
        pyautogui.rightClick()
        time.sleep(2.5) 

        last_log_time = 0

        while self.is_running:
            screen = np.array(ImageGrab.grab())
            screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

            mantar_x, mantar_y, mantar_w, mantar_h = None, None, None, None
            bulunma_yontemi = ""

            # --- YÖNTEM 1: YOLOv8 ile Arama ---
            results = self.model(screen_bgr, conf=self.confidence_level, verbose=False)
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    mantar_x, mantar_y = x1, y1
                    mantar_w, mantar_h = (x2 - x1), (y2 - y1)
                    bulunma_yontemi = "YOLO Yapay Zeka"
                    break

            # --- YÖNTEM 2: Eğer YOLO Bulamazsa, Görsel Eşleştirme (mantar.png) ile Arama ---
            if mantar_x is None and self.mantar_template is not None:
                res = cv2.matchTemplate(screen_bgr, self.mantar_template, cv2.TM_CCOEFF_NORMED)
                threshold = 0.65  # Benzerlik oranı (%65 eşleşirse kabul et)
                loc = np.where(res >= threshold)
                
                # En yüksek eşleşen noktayı al
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val >= threshold:
                    mantar_x, mantar_y = max_loc
                    mantar_h, mantar_w, _ = self.mantar_template.shape
                    bulunma_yontemi = "Görsel Eşleştirme (mantar.png)"

            # --- EĞER MANTAR BİR ŞEKİLDE BULUNDUYSA ---
            if mantar_x is not None:
                if time.time() - last_log_time > 1.5:
                    self.log_message(f"🎯 Mantar kilitlendi! [{bulunma_yontemi}]")
                    last_log_time = time.time()

                # Bulunan mantarın etrafını kes (ROI)
                padding = 50
                h, w, _ = screen_bgr.shape
                roi_y1 = max(0, mantar_y - padding)
                roi_y2 = min(h, mantar_y + mantar_h + padding)
                roi_x1 = max(0, mantar_x - padding)
                roi_x2 = min(w, mantar_x + mantar_w + padding)
                
                roi = screen_bgr[roi_y1:roi_y2, roi_x1:roi_x2]
                
                # Su partikülü takibi
                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                lower_particle = np.array([0, 0, 180])   
                upper_particle = np.array([180, 60, 255])
                mask = cv2.inRange(hsv, lower_particle, upper_particle)
                
                particle_count = np.sum(mask == 255)
                
                if particle_count > 10:  
                    self.log_message(f"🐟 Balık yakalandı! Sıçrama Yoğunluğu: {particle_count}")
                    pyautogui.rightClick()
                    time.sleep(self.click_delay)
                    
                    if not self.is_running: break
                    self.log_message("Olta suya geri fırlatılıyor...")
                    pyautogui.rightClick()
                    
                    time.sleep(3.0) 
            else:
                if time.time() - last_log_time > 2.0:
                    self.log_message("⚠️ Mantar hiçbir yöntemle bulunamadı! Kamerayı ayarlayın.")
                    last_log_time = time.time()

            time.sleep(0.1)

if __name__ == "__main__":
    app = FishingBotApp()
    app.mainloop()
        
