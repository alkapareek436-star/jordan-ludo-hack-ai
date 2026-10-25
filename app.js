
const TELEGRAM_BOT_URL = "https://t.me/Jordanludohachai_bot";

const analyzeBtn = document.getElementById("analyzeBtn");
const plans = document.getElementById("plans");

if (analyzeBtn && plans) {
  analyzeBtn.addEventListener("click", () => {
    plans.classList.remove("hidden");
    plans.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  });
}

document.querySelectorAll(".plan-card").forEach((card) => {
  card.addEventListener("click", () => {
    window.location.href = TELEGRAM_BOT_URL;
  });
});
