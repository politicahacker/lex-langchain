document.addEventListener("DOMContentLoaded", function() {
    // Injetar o botão de gravação no container de botões
    const buttonContainer = document.querySelector(".button-container");
    const recordButton = document.createElement("button");
    recordButton.id = "record-audio";
    recordButton.innerHTML = '<i class="fa fa-microphone"></i>';
    buttonContainer.appendChild(recordButton);

    var mediaRecorder;
    var audioChunks = [];

    // Inicializar MediaRecorder
    navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            var audioBlob = new Blob(audioChunks, { type: "audio/wav" });
            // Você pode enviar audioBlob para o servidor aqui
            addIndicator('Lex esta transcrevendo seu audio...')
            socket.emit('audioMessage', audioBlob);
            var audioUrl = URL.createObjectURL(audioBlob);
            var audio = new Audio(audioUrl);
            audio.play();

            audioChunks = [];
        };
    });

    // Função para começar a gravação
    function startRecording() {
        mediaRecorder.start();
        document.getElementById("record-audio").innerHTML = '<i class="fa fa-stop"></i>';
    }

    // Função para parar a gravação
    function stopRecording() {
    setTimeout(() => {
        mediaRecorder.stop();
        document.getElementById("record-audio").innerHTML = '<i class="fa fa-microphone"></i>';
    }, 300)
    }
    
    document.getElementById("record-audio").addEventListener("mousedown", function() {
        startRecording();
    });

    document.getElementById("record-audio").addEventListener("mouseup", function() {
        stopRecording();
    });
});
