document.addEventListener("DOMContentLoaded", () => {
  const result = document.querySelector(".result");
  if (result && result.textContent.includes("DENY")) {
    result.style.color = "#a60000";
  } else if (result) {
    result.style.color = "#0e6a20";
  }
});
