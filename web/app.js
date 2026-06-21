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

    const serviceButtons = document.querySelectorAll(".service-select-button");
    const serviceInput = document.getElementById("service");
    const requestSection = document.getElementById("requestSection");

    serviceButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const selectedService = button.dataset.service;

            if (serviceInput && selectedService) {
                serviceInput.value = selectedService;
            }

            if (requestSection) {
                requestSection.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }

            if (tg && tg.HapticFeedback) {
                tg.HapticFeedback.impactOccurred("light");
            }
        });
    });

    const form = document.getElementById("requestForm");

    if (!form) {
        alert("Ошибка: форма requestForm не найдена.");
        return;
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const clientNameInput = document.getElementById("clientName");
        const clientPhoneInput = document.getElementById("clientPhone");
        const serviceInput = document.getElementById("service");
        const masterInput = document.getElementById("master");
        const visitDateInput = document.getElementById("visitDate");
        const preferredTimeInput = document.getElementById("preferredTime");
        const commentInput = document.getElementById("comment");
        const submitButton = form.querySelector(".main-button");

        if (
            !clientNameInput ||
            !clientPhoneInput ||
            !serviceInput ||
            !masterInput ||
            !visitDateInput ||
            !preferredTimeInput ||
            !commentInput
        ) {
            alert("Ошибка: не найдены поля формы.");
            return;
        }

        const clientName = clientNameInput.value.trim();
        const clientPhone = clientPhoneInput.value.trim();
        const service = serviceInput.value;
        const master = masterInput.value;
        const visitDate = visitDateInput.value;
        const preferredTime = preferredTimeInput.value;
        const comment = commentInput.value.trim();

        if (!clientName) {
            if (tg) {
                tg.showAlert("Пожалуйста, укажите имя.");
            } else {
                alert("Пожалуйста, укажите имя.");
            }
            return;
        }

        if (!clientPhone) {
            if (tg) {
                tg.showAlert("Пожалуйста, укажите телефон.");
            } else {
                alert("Пожалуйста, укажите телефон.");
            }
            return;
        }

        if (!visitDate) {
            if (tg) {
                tg.showAlert("Пожалуйста, выберите дату визита.");
            } else {
                alert("Пожалуйста, выберите дату визита.");
            }
            return;
        }

        const requestData = {
            name: clientName,
            phone: clientPhone,
            service: service,
            master: master,
            visit_date: visitDate,
            preferred_time: preferredTime,
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

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Заявка отправляется...";
        }

        if (tg.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred("success");
        }

        tg.showAlert("Заявка отправляется...");

        setTimeout(function () {
            tg.sendData(jsonData);
        }, 500);
    });
});