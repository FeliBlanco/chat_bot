const express = require('express');

const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
} = require("@whiskeysockets/baileys");

const log = (pino = require("pino"));
const { session } = { session: "session_auth_info" };
const { Boom } = require("@hapi/boom");
const QRCode = require("qrcode");


const app = express();
const server = require("http").createServer(app);
const io = require("socket.io")(server);

const port = 8001;

let sock;
let qrDinamic;
let soket;

app.use("/assets", express.static(__dirname + "/client/assets"));


app.get("/send-message", async (req, res) => {
    const tempMessage = req.query.message;
    const number = req.query.number;

    let numberWA;
    try {
        if(!number) {
            res.status(500).json({
                status: false,
                response: "El numero no existe",
            })
        } else {
            numberWA = "54" + number + "@s.whatsapp.net";
            console.log(`Number: ${numberWA}`)
    
            if(isConnected()) {
                const exist = await sock.onWhatsApp(numberWA);

                if(exist?.jid || (exist && exist[0]?.jid)) {
                    sock
                    .sendMessage(exist.jid || exist[0].jid, {
                        text: tempMessage,
                    })
                    .then((result) => {
                        res.status(200).json({
                            status: true,
                            response: result,
                        });
                    })
                    .catch((err) => {
                        res.status(500).json({
                            status: false,
                            response: err,
                        });
                    });
                }
            }  else {
                res.status(500).json({
                    status: false,
                    response: "Aun no estas conectado",
                });
            }
        }
    } catch (err) {
        res.status(500).send(err);
    }
});


async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState("session_auth_info");

    sock = makeWASocket({
        auth: state,
        logger: log({ level: "silent" }),
    });

    sock.ev.on("connection.update", async (update) => {
        const { connection, lastDisconnect, qr } = update;
        if(qr) {
            console.log(await QRCode.toString(qr))
        }
        qrDinamic = qr;
        if(connection === "close") {
            let reason = new Boom(lastDisconnect.error).output.statusCode;
            if(reason === DisconnectReason.badSession) {
                sock.logout();
            } else if (reason === DisconnectReason.connectionClosed) {
                console.log("Conexión cerrada, reconectando....");
                connectToWhatsApp();
            } else if (reason === DisconnectReason.connectionLost) {
                console.log("Conexión perdida del servidor, reconectando...");
                connectToWhatsApp();
            } else if (reason === DisconnectReason.connectionReplaced) {
                console.log("Conexión reemplazada, otra nueva sesión abierta, cierre la sesión actual primero");
                sock.logout();
            } else if (reason === DisconnectReason.loggedOut) {
                console.log(
                `Dispositivo cerrado, elimínelo ${session} y escanear de nuevo.`
                );
                sock.logout();
            } else if (reason === DisconnectReason.restartRequired) {
                console.log("Se requiere reinicio, reiniciando...");
                connectToWhatsApp();
            } else if (reason === DisconnectReason.timedOut) {
                console.log("Se agotó el tiempo de conexión, conectando...");
                connectToWhatsApp();
            } else {
                sock.end(`Motivo de desconexión desconocido: ${reason}|${lastDisconnect.error}`);
            }
        } else if (connection === "open") {
            console.log("conexión abierta");
            return;
        }
    })

    sock.ev.on("messages.upsert", async ({ messages, type }) => {
        try {
            if(type === "notify") {
                if (!messages[0]?.key.fromMe) {
                    const captureMessage = messages[0]?.message?.conversation;
                    const numberWa = messages[0]?.key?.remoteJid;

                    //const compareMessage = captureMessage.toLocaleLowerCase();

                   //Por si recibe algun mensaje
                }
            }
        } catch (error) {
            console.log("error ", error);
        }
    });

    sock.ev.on("creds.update", saveCreds);
}

io.on("connection", async (socket) => {
    soket = socket;
    if(isConnected()) {
        updateQR("connected");
    } else if (qrDinamic) {
        updateQR("qr");
    }
});

const updateQR = (data) => {
    switch (data) {
        case "qr":
            qrcode.toDataURL(qrDinamic, (err, url) => {
                soket?.emit("qr", url);
                soket?.emit("log", "QR recibido , scan");
            });
            break;
        case "connected":
            soket?.emit("qrstatus", "./assets/check.svg");
            soket?.emit("log", " usaario conectado");
            const { id, name } = sock?.user;
            var userinfo = id + " " + name;
            soket?.emit("user", userinfo);
            break;
        case "loading":
            soket?.emit("qrstatus", "./assets/loader.gif");
            soket?.emit("log", "Cargando ....");
            break;
        default:
            break;
    }
};


const isConnected = () => {
    return sock?.user ? true : false;
};


connectToWhatsApp().catch((err) => console.log("unexpected error: " + err));

server.listen(port, () => {
  console.log("Server Run Port : " + port);
});