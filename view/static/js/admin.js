const flashMessage = document.querySelector(".flash-message");


if (flashMessage) {
    const timeout = 3000; // 5 seconds in milliseconds
    setTimeout(function () {
        flashMessage.remove();
    }, timeout);
}