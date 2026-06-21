document.addEventListener("DOMContentLoaded", function () {
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

    if (!form) {
        alert("Ошибка: форма requestForm не найдена.");
        return;
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const clientNameInput = document.getElementById("clientName");
        const serviceInput = document.getElementById("service");
        const commentInput = document.getElementById("comment");

        if (!clientNameInput || !serviceInput || !commentInput) {
            alert("Ошибка: не найдены поля формы.");
            return;
        }

        const clientName = clientNameInput.value.trim();
        const service = serviceInput.value;
        const comment = commentInput.value.trim();

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

        if (!tg) {
            alert(
                "Mini App открыт не внутри Telegram.\n\n" +
                "Данные не могут быть отправлены в бота."
            );
            return;
        }

        if (typeof tg.sendData !== "function") {
            tg.showAlert(
                "Mini App открыт, но способ открытия не поддерживает отправку данных.\n\n" +
                "Откройте Mini App через нижнюю кнопку Telegram."
            );
            return;
        }

        tg.showAlert("Отправляю заявку в Telegram...");

        setTimeout(function () {
            tg.sendData(jsonData);
        }, 500);
    });
});