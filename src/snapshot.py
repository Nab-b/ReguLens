"""Menulis data/data.js: salinan terbaru korpus, pembaruan, dokumen, dan log yang dapat dibaca index.html
walau aplikasi dibuka langsung sebagai berkas (tanpa server). Dipanggil otomatis setiap data berubah."""
import os, json, datetime
import sinkron, dokumen

def tulis():
    d = os.path.dirname(os.path.abspath(sinkron.KORPUS))
    dok = dokumen.daftar()
    for x in dok["dokumen"]:
        p = os.path.join(dokumen.TXT, x["id"] + ".txt")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f: x["isi"] = f.read(20000)
    obj = {"dibuat": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
           "korpus": sinkron.muat(sinkron.KORPUS, {}),
           "pembaruan": sinkron.muat(sinkron.PEMB, {"kandidat": [], "usulan": [], "tautan": []}),
           "dokumen": dok, "log": sinkron.muat(os.path.join(d, "log_sinkron.json"), [])[-30:],
           "pengaturan": sinkron.pengaturan()}
    tmp = os.path.join(d, "data.js.tmp")
    with open(tmp, "w", encoding="utf-8") as f: f.write("window.REGULENS_DATA=" + json.dumps(obj, ensure_ascii=False) + ";\n")
    os.replace(tmp, os.path.join(d, "data.js"))

if __name__ == "__main__":
    tulis(); print("data/data.js diperbarui")
