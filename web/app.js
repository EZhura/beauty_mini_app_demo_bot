const tg = window.Telegram && window.Telegram.WebApp;

if (tg) {
    tg.ready();
    tg.expand();
}

const closeAppButton = document.getElementById("closeAppButton");

if (closeAppButton) {
    closeAppButton.addEventListener("click", function () {
        if (tg) {
            tg.close();
        } else {
            alert("Это демо открыто в браузере. Закройте вкладку вручную.");
        }
    });
}

const form = document.getElementById("requestForm");

if (form) {
    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const clientName = document.getElementById("clientName").value.trim();
        const service = document.getElementById("service").value;
        const comment = document.getElementById("comment").value.trim();

        if (!clientName) {
            if (tg) {
                tg.showAlert("Пожалуйста, укажите имя.");
            } else {
                alert("Пожалуйста, укажите имя.");
            }
            return;
        }

        const requestData = {
            name: clientName,
            service: service,
            comment: comment || "Без комментария"
        };

        const jsonData = JSON.stringify(requestData);

        if (tg && tg.sendData) {
            tg.sendData(jsonData);
        } else {
            alert(
                "Демо-режим в браузере.\n\n" +
                `Имя: ${requestData.name}\n` +
                `Услуга: ${requestData.service}\n` +
                `Комментарий: ${requestData.comment}`
            );

            console.log("Данные заявки:", requestData);
        }
    });
}