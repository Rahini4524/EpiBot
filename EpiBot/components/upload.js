// -------------- BACKENT INTEGRATION -----------------


const INPUT = document.getElementById("input")
const SEND = document.getElementById("send");


SEND.addEventListener("click", ()=>{
  sendMessage(INPUT.value);
  displayUserMessage(INPUT.value);
  INPUT.value = "";
})
  

function displayUserMessage(message, isImage = false) {
  let chat = document.getElementById("chat");

  let userMessage = document.createElement("div");
  userMessage.classList.add("message", "user");

  let userAvatar = document.createElement("div");
  userAvatar.classList.add("avatar");

  let userContent = document.createElement("div");
  userContent.classList.add("text");

  if (isImage) {
      let img = document.createElement("img");
      img.src = message;
      img.style.maxWidth = "150px";
      img.style.borderRadius = "10px";
      img.style.display = "block";
      userContent.appendChild(img);
  } else {
      userContent.innerText = message;
  }

  userMessage.appendChild(userAvatar);
  userMessage.appendChild(userContent);
  chat.appendChild(userMessage);
  chat.scrollTop = chat.scrollHeight;
}

function displayBotMessage(message) {
  let chat = document.getElementById("chat");

  let botMessage = document.createElement("div");
  botMessage.classList.add("message", "bot");

  let botAvatar = document.createElement("div");
  botAvatar.classList.add("avatar");

  let botContent = document.createElement("div");
  botContent.classList.add("text");
  botContent.innerText = message;

  botMessage.appendChild(botAvatar);
  botMessage.appendChild(botContent);
  chat.appendChild(botMessage);
  chat.scrollTop = chat.scrollHeight;
}

// Handle text message sending

const sendMessage = async (user_input)=>{
  try {
      const response = await fetch("/send-message", {
          method:"POST",
          headers:{
              "Content-Type":"application/json"
          },
          body:JSON.stringify({
              message:user_input
          })
      });

      const res = await response.json();
      displayBotMessage(res.response);
      
  } catch (error) {
    console.log(error);
      alert("Something went wrong!")
  }
}
document.getElementById("input").addEventListener("keypress", function (event) {
  if (event.key === "Enter") {
      event.preventDefault(); // Prevents line break in the input field
      sendMessage(INPUT.value);
      displayUserMessage(INPUT.value);
      INPUT.value = "";
      
  }
});


// Image Upload Handling
const modal = document.getElementById("imageModal");
const cameraButton = document.getElementById("camera");
const closeModal = document.getElementById("closeModal");
const uploadBtn = document.getElementById("upload-btn");
const imageInput = document.getElementById("image_input");

// Open modal when clicking the camera button
cameraButton.addEventListener("click", function () {
  modal.style.display = "flex";
  document.body.classList.add("modal-open");
});

// Close modal when clicking 'X' button
closeModal.addEventListener("click", function () {
  modal.style.display = "none";
  document.body.classList.remove("modal-open");
});

// Close modal when clicking outside content
window.addEventListener("click", function (event) {
  if (event.target === modal) {
      modal.style.display = "none";
      document.body.classList.remove("modal-open");
  }
});

// Open file selector when clicking upload button
uploadBtn.addEventListener("click", function () {
  imageInput.click();
});

// Handle image upload
imageInput.addEventListener("change", function () {
  const file = this.files[0];

  if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
          modal.style.display = "none";
          document.body.classList.remove("modal-open");

          // Display user-uploaded image
          displayUserMessage(e.target.result, true);

          // Bot response after 1 second
          setTimeout(() => {
              displayBotMessage("I see you've uploaded an image! Let me analyze it...");
          }, 1000);
      };
      reader.readAsDataURL(file);
  }
});

// Simulated bot typing effect
function typeEffect(element, text, speed = 50) {
  let i = 0;
  element.innerHTML = "";

  function type() {
      if (i < text.length) {
          element.innerHTML += text.charAt(i);
          i++;
          setTimeout(type, speed);
      }
  }

  type();
}

// Initialize bot welcome message on page load
document.addEventListener("DOMContentLoaded", function () {
  const botTextElement = document.getElementById("bot-text");
  const message = `Welcome to Epibot! 🤖 Upload an image and I'll analyze it. Let's get started!`;
  typeEffect(botTextElement, message, 30);

});




