document.addEventListener("DOMContentLoaded", function () {
    const tg = window.Telegram && window.Telegram.WebApp;
    let currentLanguage = "ru";

    if (tg) {
        tg.ready();
        tg.expand();
    }

    function applyLanguage(language) {
        currentLanguage = language;

        document.documentElement.lang = language;

        const languageButtons = document.querySelectorAll(".lang-button");

        languageButtons.forEach(function (button) {
            if (button.dataset.lang === language) {
                button.classList.add("active");
            } else {
                button.classList.remove("active");
            }
        });

        const translatableElements = document.querySelectorAll("[data-ru][data-en]");

        translatableElements.forEach(function (element) {
            const text = element.dataset[language];

            if (text) {
                element.textContent = text;
            }
        });

        const placeholderElements = document.querySelectorAll("[data-placeholder-ru][data-placeholder-en]");

        placeholderElements.forEach(function (element) {
            const placeholder = element.dataset["placeholder" + capitalize(language)];

            if (placeholder) {
                element.setAttribute("placeholder", placeholder);
            }
        });

        updateSelectTextsAfterLanguageChange();
    }

    function capitalize(value) {
        return value.charAt(0).toUpperCase() + value.slice(1);
    }

    const langButtons = document.querySelectorAll(".lang-button");

    langButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const selectedLanguage = button.dataset.lang || "ru";
            applyLanguage(selectedLanguage);

            if (tg && tg.HapticFeedback) {
                tg.HapticFeedback.impactOccurred("light");
            }
        });
    });

    const closeAppButton = document.getElementById("closeAppButton");

    if (closeAppButton) {
        closeAppButton.addEventListener("click", function () {
            if (tg) {
                tg.close();
            } else {
                alert(currentLanguage === "ru" ?
                    "Это демо открыто в браузере. Закройте вкладку вручную." :
                    "This demo is opened in a browser. Please close the tab manually."
                );
            }
        });
    }

    const today = new Date().toISOString().split("T")[0];
    const visitDateInput = document.getElementById("visitDate");

    if (visitDateInput) {
        visitDateInput.setAttribute("min", today);
    }

    function scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

        if (tg && tg.HapticFeedback) {
            tg.HapticFeedback.impactOccurred("light");
        }
    }

    function scrollToSection(targetId) {
        const target = document.getElementById(targetId);

        if (target) {
            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

            if (tg && tg.HapticFeedback) {
                tg.HapticFeedback.impactOccurred("light");
            }
        }
    }

    const scrollButtons = document.querySelectorAll("[data-scroll-target]");

    scrollButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const targetId = button.dataset.scrollTarget;
            scrollToSection(targetId);
        });
    });

    const scrollTopButtons = document.querySelectorAll("[data-scroll-top]");

    scrollTopButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            scrollToTop();
        });
    });

    const categoryTabs = document.querySelectorAll(".category-tab");
    const serviceCards = document.querySelectorAll(".service-card");

    categoryTabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            const selectedCategory = tab.dataset.category;

            categoryTabs.forEach(function (item) {
                item.classList.remove("active");
            });

            tab.classList.add("active");

            serviceCards.forEach(function (card) {
                if (selectedCategory === "all" || card.dataset.category === selectedCategory) {
                    card.classList.remove("hidden");
                } else {
                    card.classList.add("hidden");
                }
            });
        });
    });

    const serviceButtons = document.querySelectorAll(".service-select-button");
    const requestSection = document.getElementById("requestSection");

    serviceButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const selectedService = getLocalizedServiceName(button);

            if (selectedService) {
                setServiceSelectValue(selectedService);
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

    function getLocalizedServiceName(button) {
        if (currentLanguage === "en") {
            return button.dataset.serviceEn || button.dataset.serviceRu || "";
        }

        return button.dataset.serviceRu || button.dataset.serviceEn || "";
    }

    function setServiceSelectValue(serviceName) {
        const serviceSelect = document.getElementById("service");

        if (!serviceSelect) {
            return;
        }

        const options = serviceSelect.querySelectorAll("option");

        options.forEach(function (option) {
            const optionText = currentLanguage === "en" ?
                option.dataset.en :
                option.dataset.ru;

            if (optionText === serviceName) {
                serviceSelect.value = option.value;
            }
        });
    }

    function getVisibleSelectText(selectElement) {
        if (!selectElement) {
            return "";
        }

        const selectedOption = selectElement.options[selectElement.selectedIndex];

        if (!selectedOption) {
            return "";
        }

        if (currentLanguage === "en") {
            return selectedOption.dataset.en || selectedOption.textContent;
        }

        return selectedOption.dataset.ru || selectedOption.textContent;
    }

    function updateSelectTextsAfterLanguageChange() {
        const selects = document.querySelectorAll("select");

        selects.forEach(function (selectElement) {
            const options = selectElement.querySelectorAll("option");

            options.forEach(function (option) {
                const text = currentLanguage === "en" ?
                    option.dataset.en :
                    option.dataset.ru;

                if (text) {
                    option.textContent = text;
                }
            });
        });
    }

    const googleMapsButton = document.getElementById("googleMapsButton");

    if (googleMapsButton) {
        googleMapsButton.addEventListener("click", function () {
            const mapsUrl = "https://www.google.com/maps/search/?api=1&query=beauty%20salon";

            if (tg) {
                tg.openLink(mapsUrl);
            } else {
                window.open(mapsUrl, "_blank");
            }
        });
    }

    const onlineBookingDemoButton = document.getElementById("onlineBookingDemoButton");

    if (onlineBookingDemoButton) {
        onlineBookingDemoButton.addEventListener("click", function () {
            const text = currentLanguage === "ru" ?
                "В рабочей версии эта кнопка может вести на сайт, Instagram, Google Maps, YCLIENTS, CRM или другую систему записи." :
                "In a real version, this button can lead to a website, Instagram, Google Maps, YCLIENTS, CRM or another booking system.";

            if (tg) {
                tg.showAlert(text);
            } else {
                alert(text);
            }
        });
    }

    const faqItems = document.querySelectorAll(".faq-item");

    faqItems.forEach(function (item) {
        item.addEventListener("click", function () {
            const answer = item.nextElementSibling;
            const icon = item.querySelector("strong");

            if (!answer) {
                return;
            }

            answer.classList.toggle("open");

            if (icon) {
                icon.textContent = answer.classList.contains("open") ? "−" : "+";
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
            alert(currentLanguage === "ru" ?
                "Ошибка: не найдены поля формы." :
                "Error: form fields not found."
            );
            return;
        }

        const clientName = clientNameInput.value.trim();
        const clientPhone = clientPhoneInput.value.trim();
        const service = getVisibleSelectText(serviceInput);
        const master = getVisibleSelectText(masterInput);
        const visitDate = visitDateInput.value;
        const preferredTime = getVisibleSelectText(preferredTimeInput);
        const comment = commentInput.value.trim();

        if (!clientName) {
            showMessage(currentLanguage === "ru" ?
                "Пожалуйста, укажите имя." :
                "Please enter your name."
            );
            return;
        }

        if (!clientPhone) {
            showMessage(currentLanguage === "ru" ?
                "Пожалуйста, укажите телефон." :
                "Please enter your phone number."
            );
            return;
        }

        if (!visitDate) {
            showMessage(currentLanguage === "ru" ?
                "Пожалуйста, выберите дату визита." :
                "Please choose a visit date."
            );
            return;
        }

        const requestData = {
            language: currentLanguage,
            name: clientName,
            phone: clientPhone,
            service: service,
            master: master,
            visit_date: visitDate,
            preferred_time: preferredTime,
            comment: comment || (currentLanguage === "ru" ? "Без комментария" : "No comment")
        };

        const jsonData = JSON.stringify(requestData);

        if (!tg) {
            alert(currentLanguage === "ru" ?
                "Mini App открыт не внутри Telegram.\n\nДанные не могут быть отправлены в бота." :
                "Mini App is not opened inside Telegram.\n\nThe data cannot be sent to the bot."
            );
            return;
        }

        if (typeof tg.sendData !== "function") {
            tg.showAlert(currentLanguage === "ru" ?
                "Mini App открыт, но способ открытия не поддерживает отправку данных.\n\nОткройте Mini App через нижнюю кнопку Telegram." :
                "Mini App is opened, but this opening method does not support data sending.\n\nPlease open Mini App through the bottom Telegram button."
            );
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = currentLanguage === "ru" ?
                "Заявка отправлена ✓" :
                "Request sent ✓";
        }

        if (tg.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred("success");
        }

        tg.sendData(jsonData);

        setTimeout(function () {
            tg.close();
        }, 700);
    });

    function showMessage(text) {
        if (tg) {
            tg.showAlert(text);
        } else {
            alert(text);
        }
    }

    applyLanguage("ru");
});