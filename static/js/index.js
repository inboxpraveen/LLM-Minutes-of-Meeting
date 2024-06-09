document.addEventListener('DOMContentLoaded', (event) => {

    const notificationModel = document.getElementById("notificationModel");
    const notificationButton = document.getElementById("notificationButton");
    const notificationCloseButton = document.getElementById("notificationCloseButton");

    notificationButton.onclick = function() {
        notificationModel.style.display = "block";
        if ($('#notif-text').text().trim() === '') {
            $('#notif-text').text('<li>No new notifications</li>');
        }
    }

    notificationCloseButton.onclick = function() {
        notificationModel.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == notificationModel) {
            notificationModel.style.display = "none";
        }
    }

    const meetingModal = document.getElementById("meetingModal");
    const meetingButton = document.getElementById("meetingButton");
    const meetingCloseButton = document.getElementById("meetingCloseButton");

    meetingButton.onclick = function() {
        meetingModal.style.display = "block";
    }

    meetingCloseButton.onclick = function() {
        meetingModal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == meetingModal) {
            meetingModal.style.display = "none";
        }
    }
});
