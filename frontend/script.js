const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const messages = document.getElementById("messages");
const button = form.querySelector("button");

function addMessage(text, role) {
  const element = document.createElement("div");
  element.className = "message " + role;
  element.textContent = text;
  messages.appendChild(element);
  element.scrollIntoView({ behavior: "smooth" });
  return element;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = input.value.trim();
  if (!question) return;

  addMessage(question, "user");
  input.value = "";
  button.disabled = true;

  const loading = addMessage("Analyzing procurement data...", "assistant");

  try {
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }

    loading.textContent = data.answer;
  } catch (error) {
    loading.textContent = "Error: " + error.message;
  } finally {
    button.disabled = false;
    input.focus();
  }
});
