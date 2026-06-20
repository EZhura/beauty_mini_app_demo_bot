const tg = window.Telegram.WebApp;

tg.expand();

const form = document.getElementById("requestForm");

form.addEventListener("submit", function (event) {
    event.preventDefault();

    const clientName = document.getElementById("clientName").value.trim();
    const service = document.getElementById("service").value;
    const comment = document.getElementById("comment").value.trim();

    if (!clientName) {
        tg.showAlert("Пожалуйста, укажите имя.");
        return;
    }

    const requestData = {
        name: clientName,
        service: service,
        comment: comment || "Без комментария"
    };

    tg.showAlert(
        `Заявка подготовлена:\n\nИмя: ${requestData.name}\nУслуга: ${requestData.service}`
    );

    console.log("Данные заявки:", requestData);
});