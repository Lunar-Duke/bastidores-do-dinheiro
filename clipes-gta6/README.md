# Canal de clipes de GTA 6

GTA 6 sai em 19/11/2026 (PS5 e Xbox Series). Nas primeiras semanas, todo streamer grande vai jogar e a busca por "GTA 6" vai explodir. Esse é o momento de entrar.

O `clipar.py` pega um trecho de live (Twitch, YouTube, Kick ou arquivo) e entrega um Short 1080x1920 pronto. Ele faz o layout vertical, põe o gancho no topo, gera legenda palavra por palavra, mixa a sua narração e ajusta o volume ao padrão do YouTube (-14 LUFS).

## Instalar (uma vez)

Precisa de Python 3.10+ e ffmpeg no PATH (no Windows: `winget install ffmpeg`).

```
pip install -r requirements.txt
python clipar.py --teste
```

## Usar

```
# 1. Layout simples (fundo desfocado), só gancho
python clipar.py https://www.twitch.tv/videos/123456789 --de 1:02:10 --ate 1:02:45 --gancho "ELE ROUBOU O BANCO SOZINHO" -o saida/banco.mp4

# 2. Webcam em cima, gameplay embaixo, com legenda (o formato que mais segura)
python clipar.py LINK --de 2:14:05 --ate 2:14:40 --cam 0.75:0.05:0.22:0.25 --legenda --gancho "A POLÍCIA NÃO ACREDITOU" -o saida/policia.mp4

# 3. Com a sua narração por cima (o que torna o vídeo SEU, ver "Monetização")
python clipar.py LINK --de 40:00 --ate 40:35 --cam ... --narracao voz.mp3 --gancho "..." -o saida/x.mp4
```

`--cam x:y:largura:altura` é a posição da webcam na tela original, em frações. Uma webcam no canto superior direito ocupando ~22% da largura fica `0.75:0.05:0.22:0.25`. Descubra uma vez por streamer e reaproveite.

A legenda usa Whisper. Na primeira vez ele baixa o modelo (~500 MB no `small`). Use `--modelo base` se o PC for fraco ou `--modelo medium` para mais precisão.

## Como o algoritmo decide (o que importa de verdade)

**Shorts.** O feed testa cada Short com um grupo pequeno. Se for bem, ele mostra para um grupo maior, depois maior.
"Ir bem" é principalmente:
1. **Assistiu vs. passou o dedo** (taxa de visualização). Esse é o portão. Se a pessoa passa nos primeiros 1-2 segundos, o vídeo morre. Por isso o clipe começa **no meio da ação**, nunca no "e aí, galera".
2. **Retenção e loop.** Mais de 100% de visualização média acontece quando o vídeo termina e recomeça sem a pessoa perceber. Corte o final colado no começo, ou termine na reação.
3. **Sinais de interesse.** Curtida, comentário, compartilhamento, inscrição a partir do Short. Uma pergunta no gancho ("Quem faria isso?") puxa comentário.

**Vídeos longos.** O peso é CTR da thumbnail × tempo assistido, e satisfação (pesquisas e se a pessoa volta). Um compilado semanal "Os momentos mais insanos do GTA 6 da semana" (8 a 12 min) é a melhor ponte de Short para inscrito fiel.

**Canal novo.** O YouTube não sabe para quem mostrar você. Os primeiros 20 a 30 Shorts ensinam isso. Fique num nicho só (GTA 6, em português) para o público-semente ser o certo. Não misture com outros jogos agora.

**Busca e tendência.** Nas primeiras semanas a busca por "GTA 6 + coisa específica" é enorme. Título com o termo que a pessoa digita: "GTA 6: o assalto ao banco de Vice City", "GTA 6 easter egg", "GTA 6 polícia".

## Plano dos primeiros 14 dias

- **Volume:** 3 a 5 Shorts por dia. Quem posta primeiro o momento viral leva a maior parte das views. Velocidade vale mais que perfeição.
- **De onde vêm os clipes:** os streamers brasileiros maiores jogando no lançamento, mais as lives de madrugada (menos concorrência para clipar).
- **Escolha do trecho:** reação forte (grito, risada), algo que dá errado de forma engraçada, descoberta (easter egg, detalhe absurdo do mapa), perseguição, bug.
- **Duração:** 20 a 50 s. Corte tudo que não é ação.
- **Gancho no topo:** até 6 palavras, em caixa alta, dizendo o que vai acontecer sem entregar o final.
- **Título:** gancho + "GTA 6" + nome do streamer (quem busca o streamer acha você). Ex.: "Fulano tentou roubar o banco no GTA 6 e deu tudo errado".
- **Horário:** publique perto do fim das lives grandes (o pico de procura vem depois), e nunca deixe um dia sem post.
- **Olhe o painel a cada 2 dias:** em "Alcance" > "Visualizações vs. deslizadas". Abaixo de ~60% assistiu, o começo está fraco. Repita os formatos que passarem de 70%.

## Monetização e direitos: leia antes de postar

Isso é o que derruba canal de clipes. Duas regras diferentes:

1. **Direito autoral.** O vídeo da live é do streamer. **Peça permissão.** Muitos streamers BR deixam clipar (alguns até pagam clipadores). Mande DM ou entre no Discord da comunidade e pergunte. Ponha o crédito na descrição e no título. Sem permissão, um pedido de remoção dá strike, e com 3 strikes o canal cai.
2. **Conteúdo reutilizado (monetização).** Mesmo **com** permissão, o YouTube não monetiza um canal de clipes cortados sem nada novo. Essa regra vale para o canal inteiro, não para um vídeo. Em 2026 o YouTube também está distribuindo menos os Shorts repostados. O que conta como "seu": a sua narração ou comentário (`--narracao`), contexto, ou história contada em cima. Legenda e gancho ajudam, mas sozinhos não bastam.

Regra prática: comece já com clipes + gancho + legenda para crescer, e em paralelo grave narração curta ("Olha o que ele fez aqui...") em parte dos vídeos. Antes de pedir a monetização, o canal precisa ter uma maioria de vídeos com a sua voz.

Não poste vazamentos nem material de antes do lançamento. A Rockstar derruba esse conteúdo.

## Enviar e agendar

A Fabrica Canal (a ferramenta que você usa no Bastidores do Dinheiro) já envia e agenda pela API do YouTube. Use a mesma ferramenta para este canal: autorize com o login do canal novo. Se o projeto do Google Cloud for o mesmo, atualize a política de privacidade em `privacidade.html` para citar os dois canais.
