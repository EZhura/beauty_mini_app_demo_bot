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

        const clientNameInput = document.getElementById("clientName");
        const serviceInput = document.getElementById("service");
        const commentInput = document.getElementById("comment");

        if (!clientNameInput || !serviceInput || !commentInput) {
            alert("Ошибка формы: не найдены поля заявки.");
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

        console.log("Данные заявки:", requestData);
        console.log("Telegram WebApp object:", tg);

        if (tg && typeof tg.sendData === "function") {
            tg.sendData(jsonData);
        } else {
            alert(
                "Заявка НЕ отправлена в Telegram.\n\n" +
                "Скорее всего, Mini App открыт как обычная страница, а не через кнопку Telegram Web App.\n\n" +
                `Имя: ${requestData.name}\n` +
                `Услуга: ${requestData.service}\n` +
                `Комментарий: ${requestData.comment}`
            );
        }
    });
} else {
    alert("Форма заявки не найдена на странице.");
}