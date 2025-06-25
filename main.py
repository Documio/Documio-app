import os
import openai
import gradio as gr
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# 🔐 OpenAI-Client initialisieren
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🎙 Transkription
def transkribieren(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcription.text

# 🧠 GPT-Analyse
def generiere_befund(transkript):
    prompt = f"""
    Du bist ein medizinischer Dokumentationsassistent. Erstelle aus folgendem Transkript einen strukturierten ärztlichen Befundbericht.

    Regeln:
    - Keine Namen
    - Nutze "der Patient" oder "die Patientin"
    - Kein Smalltalk
    - Kein "ich empfehle", sondern "Es wird empfohlen …"

    Struktur:
    1. Symptome
    2. Diagnose oder Verdachtsdiagnose
    3. Therapieempfehlung
    4. Abschluss

    Stil: medizinisch, sachlich.

    TRANSKRIPT:
    {transkript}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# 📄 PDF-Erstellung
def erstelle_pdf(praxis, patient, geburt, befund):
    datum = datetime.today().strftime("%Y-%m-%d")
    dateiname = f"{datum}_Befund_{patient.replace(' ', '_')}.pdf"
    pfad = os.path.join(os.getcwd(), dateiname)

    c = canvas.Canvas(pfad, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "Documio – Ärztlicher Befundbericht")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Praxis: {praxis}")
    y -= 20
    c.drawString(50, y, f"Patient: {patient}")
    y -= 20
    c.drawString(50, y, f"Geburtsdatum: {geburt}")
    y -= 20
    c.drawString(50, y, f"Datum: {datum}")
    y -= 30

    for abschnitt in befund.split("\n"):
        for zeile in abschnitt.strip().split(". "):
            c.drawString(50, y, zeile.strip())
            y -= 15
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height - 50

    c.save()
    return pfad

# 🔁 Gesamtprozess
def documio(audio, praxis, patient, geburt, einwilligung):
    if not einwilligung:
        return "⚠️ DSGVO-Einwilligung erforderlich.", None
    try:
        transkript = transkribieren(audio)
        befund = generiere_befund(transkript)
        pdf = erstelle_pdf(praxis, patient, geburt, befund)
        return befund, pdf
    except Exception as e:
        return f"❌ Fehler: {str(e)}", None

# 🖥️ Benutzeroberfläche
with gr.Blocks() as app:
    gr.Markdown("# 🩺 **Documio**")
    gr.Markdown("### Vom Gespräch zum Befund. In Sekunden.")

    gr.Markdown("---")
    gr.Markdown("✅ Diese Anwendung verwandelt ein Arzt-Patient-Gespräch in einen strukturierten ärztlichen Befundbericht.")
    gr.Markdown("📄 Die Ausgabe erfolgt sofort als professionelles PDF-Dokument – bereit für die Patientenakte.")

    with gr.Row():
        praxis_input = gr.Textbox(label="🏥 Praxisname", placeholder="z. B. Hausarztpraxis Dr. Meier")
        name_input = gr.Textbox(label="👤 Patientenname", placeholder="z. B. Max Müller")

    with gr.Row():
        geburt_input = gr.Textbox(label="🎂 Geburtsdatum", placeholder="TT.MM.JJJJ")
        audio_input = gr.Audio(type="filepath", label="🎙 Gespräch hochladen (MP3/WAV)")

    zustimmung = gr.Checkbox(label="✅ DSGVO-Einwilligung zur Analyse liegt vor", value=False)

    starten = gr.Button("🧠 Analyse starten")
    befund_output = gr.Textbox(label="📋 Automatisch generierter Befundbericht", lines=12, interactive=False)
    pdf_output = gr.File(label="📄 PDF herunterladen")

    starten.click(fn=documio,
                  inputs=[audio_input, praxis_input, name_input, geburt_input, zustimmung],
                  outputs=[befund_output, pdf_output])

app.launch(share=True)