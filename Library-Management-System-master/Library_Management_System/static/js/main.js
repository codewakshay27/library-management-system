function openLogin() {

    document.getElementById("loginModal").style.display = "flex";
    document.getElementById("registerModal").style.display = "none";

}

function openRegister() {

    document.getElementById("registerModal").style.display = "flex";
    document.getElementById("loginModal").style.display = "none";

}

function switchToRegister() {

    openRegister();

}

function switchToLogin() {

    openLogin();

}

window.onclick = function (e) {

    if (e.target.classList.contains("modal-overlay")) {

        e.target.style.display = "none";

    }

}
function openBook() {

    document.getElementById("loginModal").style.display = "flex";

}

function closeLogin() {

    document.getElementById("loginModal").style.display = "none";

}

function flipBook() {

    document.getElementById("bookBox").classList.toggle("flip");

    document.getElementById("bookBox").classList.toggle("rotate-y-180");


}
function toggleProfileSidebar() {
    const sidebar = document.getElementById("profileSidebar");
    sidebar.classList.toggle("active");
    sidebar.classList.toggle("translate-x-full");
}
function toggleAdminSidebar() {
    const sidebar = document.getElementById("adminSidebar");
    sidebar.classList.toggle("translate-x-full");
    sidebar.classList.toggle("active");
}
function openRegister() {
    document.getElementById("loginModal").style.display = "flex";

    const book = document.getElementById("bookBox");

    if (!book.classList.contains("flip")) {
        book.classList.add("flip");
    }
}
