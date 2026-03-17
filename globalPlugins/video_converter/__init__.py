import os
import subprocess
import threading
import globalPluginHandler
import ui
import wx
import tones
import gui

class FormatDialog(wx.Dialog):
	def __init__(self, parent, video_path, callback):
		super(FormatDialog, self).__init__(parent, title="Audio Extractor")
		self.video_path = video_path
		self.callback = callback
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		fileName = os.path.basename(video_path)
		label = wx.StaticText(self, label=f"Select output format for:\n{fileName}")
		mainSizer.Add(label, 0, wx.ALL, 10)
		
		# Radio Buttons
		self.mp3Radio = wx.RadioButton(self, label="MP3 (Standard Quality - 192kbps)", style=wx.RB_GROUP)
		self.wavRadio = wx.RadioButton(self, label="WAV (High Quality - Lossless)")
		mainSizer.Add(self.mp3Radio, 0, wx.LEFT, 20)
		mainSizer.Add(self.wavRadio, 0, wx.LEFT, 20)
		
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.confBtn = wx.Button(self, label="Extract")
		self.confBtn.SetDefault()
		self.cancelBtn = wx.Button(self, wx.ID_CANCEL, label="Cancel")
		
		btnSizer.Add(self.confBtn, 0, wx.ALL, 5)
		btnSizer.Add(self.cancelBtn, 0, wx.ALL, 5)
		
		mainSizer.Add(btnSizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
		self.SetSizer(mainSizer)
		mainSizer.Fit(self)
		
		self.confBtn.Bind(wx.EVT_BUTTON, self.on_go)
		self.mp3Radio.SetFocus()

	def on_go(self, event):
		fmt = "mp3" if self.mp3Radio.GetValue() else "wav"
		self.EndModal(wx.ID_OK)
		self.callback(self.video_path, fmt)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def script_doExtract(self, gesture):
		if not wx.TheClipboard.IsOpened():
			wx.TheClipboard.Open()
			data = wx.FileDataObject()
			success = wx.TheClipboard.GetData(data)
			wx.TheClipboard.Close()
			
			if not success:
				ui.message("Clipboard is empty")
				return
			
			files = data.GetFilenames()
			if not files or len(files) == 0:
				ui.message("No file detected in clipboard")
				return
			
			path = os.path.normpath(files[0])
			ext = os.path.splitext(path)[1].lower()
			supported = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.3gp', '.mpeg', '.mpg', '.m4v']
			if ext not in supported:
				ui.message(f"File format {ext} is not supported")
				return

			wx.CallAfter(self.open_ui, path)

	def open_ui(self, path):
		dlg = FormatDialog(gui.mainFrame, path, self.start_proc)
		dlg.ShowModal()
		dlg.Destroy()

	def start_proc(self, path, fmt):
		ext = ".mp3" if fmt == "mp3" else ".wav"
		prm = ["-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k"] if fmt == "mp3" else ["-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2"]
		
		output_path = os.path.splitext(path)[0] + ext
		exe = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
		
		if not os.path.exists(exe):
			ui.message("FFmpeg not found in plugin folder")
			return

		tones.beep(440, 200)
		ui.message(f"Extracting to {fmt.upper()}...")
		t = threading.Thread(target=self.run_ffmpeg, args=(exe, path, output_path, prm))
		t.start()

	def run_ffmpeg(self, exe, inp, out, prm):
		try:
			cmd = [exe, "-i", inp] + prm + ["-y", out]
			si = subprocess.STARTUPINFO()
			si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			res = subprocess.Popen(cmd, startupinfo=si).wait()
			
			if res == 0:
				tones.beep(880, 250)
				ui.message("Extraction completed")
			else:
				ui.message("Extraction failed")
		except Exception:
			ui.message("System execution error")

	__gestures = {
		"kb:nvda+alt+v": "doExtract",
	}