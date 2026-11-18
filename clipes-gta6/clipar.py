"""Corta um trecho de live (Twitch, YouTube, Kick ou arquivo local) e entrega um Short 1080x1920 pronto.

Uso:
  python clipar.py URL_OU_ARQUIVO --de 1:02:10 --ate 1:02:45 --gancho "ELE ROUBOU O BANCO SOZINHO"
  python clipar.py ... --cam 0.75:0.05:0.22:0.25   # webcam em cima, gameplay embaixo
  python clipar.py ... --legenda                    # legendas automáticas palavra por palavra
  python clipar.py ... --narracao minha_voz.mp3     # sua voz por cima (o que torna o vídeo original)
  python clipar.py --teste                          # autoteste com vídeo sintético
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

W, H = 1080, 1920
CAM_H = 640  # altura da webcam no layout dividido; o resto (1280) é gameplay


def segundos(t):
    s = 0.0
    for parte in str(t).split(":"):
        s = s * 60 + float(parte)
    return s


def ff(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def obter_trecho(fonte, de, ate, pasta):
    """Devolve um mp4 só com o trecho pedido, começando em 0."""
    destino = pasta / "corte.mp4"
    if Path(fonte).exists():
        ff("-ss", str(de), "-to", str(ate), "-i", fonte, "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", "-c:a", "aac", str(destino))
        return destino
    import yt_dlp
    opts = {
        "outtmpl": str(pasta / "corte.%(ext)s"),
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "download_ranges": yt_dlp.utils.download_range_func(None, [(segundos(de), segundos(ate))]),
        "force_keyframes_at_cuts": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([fonte])
    return next(pasta.glob("corte.*"))


def tem_audio(arquivo):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                          "-of", "json", str(arquivo)], capture_output=True, text=True, check=True).stdout
    return bool(json.loads(out).get("streams"))


def ass_tempo(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_texto(t):
    return re.sub(r"[{}\\\n]", " ", t).strip()


def transcrever(arquivo, idioma, modelo):
    from faster_whisper import WhisperModel
    segs, _ = WhisperModel(modelo, compute_type="int8").transcribe(str(arquivo), language=idioma, word_timestamps=True)
    palavras = [w for s in segs for w in s.words]
    blocos = []  # 3 palavras por vez: o estilo que segura retenção em Short
    for i in range(0, len(palavras), 3):
        grupo = palavras[i:i + 3]
        blocos.append((grupo[0].start, grupo[-1].end, " ".join(w.word.strip() for w in grupo).upper()))
    return blocos


def montar_ass(caminho, gancho, blocos, duracao):
    linhas = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV",
        # gancho: faixa amarela no topo; legenda: branco com contorno grosso no meio da tela
        "Style: Gancho,Arial Black,72,&H00000000,&H0000D7FF,&H0000D7FF,1,3,18,0,8,60,60,90",
        "Style: Legenda,Arial Black,88,&H00FFFFFF,&H00000000,&H80000000,1,1,8,3,5,60,60,0",
        "", "[Events]", "Format: Layer, Start, End, Style, Text",
    ]
    if gancho:
        linhas.append(f"Dialogue: 1,{ass_tempo(0)},{ass_tempo(duracao)},Gancho,{ass_texto(gancho).upper()}")
    for ini, fim, texto in blocos:
        linhas.append(f"Dialogue: 0,{ass_tempo(ini)},{ass_tempo(fim)},Legenda,{ass_texto(texto)}")
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def duracao_de(arquivo):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arquivo)],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def renderizar(corte, saida, cam, ass, narracao):
    if cam:
        cx, cy, cw, ch = (float(v) for v in cam.split(":"))
        video = (f"[0:v]crop=iw*{cw}:ih*{ch}:iw*{cx}:ih*{cy},scale={W}:{CAM_H}:force_original_aspect_ratio=increase,"
                 f"crop={W}:{CAM_H}[cam];"
                 f"[0:v]crop=ih*{W}/{H - CAM_H}:ih,scale={W}:{H - CAM_H}[jogo];[cam][jogo]vstack[base]")
    else:
        video = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=40[fundo];"
                 f"[0:v]scale={W}:-2[frente];[fundo][frente]overlay=(W-w)/2:(H-h)/2[base]")
    # caminho do .ass escapado para o filtro do ffmpeg (Windows tem "C:")
    ass_f = str(ass).replace("\\", "/").replace(":", r"\:")
    grafo = f"{video};[base]subtitles='{ass_f}',setsar=1[v]"

    entradas = ["-i", str(corte)]
    if narracao:
        entradas += ["-i", narracao]
        # narração na frente, áudio da live abaixado por baixo
        grafo += ";[0:a]volume=0.3[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1[a]"
    else:
        grafo += ";[0:a]loudnorm=I=-14:TP=-1[a]"
    ff(*entradas, "-filter_complex", grafo, "-map", "[v]", "-map", "[a]", "-r", "30",
       "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(saida))


def clipar(fonte, de, ate, saida, gancho="", cam=None, legenda=False, narracao=None, idioma="pt", modelo="small"):
    if segundos(ate) <= segundos(de):
        sys.exit("--ate precisa ser depois de --de")
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        corte = obter_trecho(fonte, de, ate, pasta)
        if not tem_audio(corte):
            sys.exit("O trecho não tem áudio.")
        dur = duracao_de(corte)
        if dur > 180:
            print(f"Aviso: {dur:.0f}s. Short aceita até 3 min, mas clipe de GTA rende mais com 20 a 50s.")
        blocos = transcrever(corte, idioma, modelo) if legenda else []
        ass = pasta / "texto.ass"
        montar_ass(ass, gancho, blocos, dur)
        Path(saida).parent.mkdir(parents=True, exist_ok=True)
        renderizar(corte, saida, cam, ass, narracao)
    print(f"Pronto: {saida}")


def autoteste():
    def dims(f):
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                              "-of", "csv=p=0", str(f)], capture_output=True, text=True, check=True).stdout
        return out.strip()

    assert segundos("1:02:03") == 3723 and segundos("45") == 45 and segundos("1:30.5") == 90.5
    assert ass_tempo(3723.5) == "1:02:03.50"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        fonte = p / "live.mp4"
        ff("-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30:duration=12", "-f", "lavfi",
           "-i", "sine=frequency=440:duration=12", "-shortest", "-c:v", "libx264", "-c:a", "aac", str(fonte))
        voz = p / "voz.wav"
        ff("-f", "lavfi", "-i", "sine=frequency=220:duration=5", str(voz))
        clipar(str(fonte), "2", "8", p / "a.mp4", gancho="teste {com} chaves")
        clipar(str(fonte), "0:02", "0:08", p / "b.mp4", gancho="dividido", cam="0.75:0.05:0.22:0.25", narracao=str(voz))
        for f in ("a.mp4", "b.mp4"):
            assert dims(p / f) == "1080,1920", dims(p / f)
            assert 5.5 < duracao_de(p / f) < 6.5, duracao_de(p / f)
    print("Autoteste ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Live -> Short vertical pronto")
    ap.add_argument("fonte", nargs="?", help="link da live/clipe/VOD ou arquivo local")
    ap.add_argument("--de", help="início do trecho (ex.: 1:02:10)")
    ap.add_argument("--ate", help="fim do trecho (ex.: 1:02:45)")
    ap.add_argument("--gancho", default="", help="frase curta no topo, aparece o vídeo todo")
    ap.add_argument("--cam", help="webcam na fonte, em frações x:y:largura:altura (ex.: 0.75:0.05:0.22:0.25)")
    ap.add_argument("--legenda", action="store_true", help="legenda automática com Whisper")
    ap.add_argument("--narracao", help="áudio com a sua voz para pôr por cima")
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--modelo", default="small", help="modelo do Whisper: tiny, base, small, medium")
    ap.add_argument("-o", "--saida", default="saida/short.mp4")
    ap.add_argument("--teste", action="store_true")
    a = ap.parse_args()
    if a.teste:
        autoteste()
    elif not (a.fonte and a.de and a.ate):
        ap.error("informe a fonte, --de e --ate")
    else:
        clipar(a.fonte, a.de, a.ate, a.saida, a.gancho, a.cam, a.legenda, a.narracao, a.idioma, a.modelo)
