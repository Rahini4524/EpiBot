function displayUserMessage(message){
  let chat = document.getElementById('chat')

  let usermessage = document.createElement('div')
  usermessage.classList.add('message')
  usermessage.classList.add('user')

  let userAvatar = document.createElement("div");
  userAvatar.classList.add("avatar");

  let userText = document.createElement("div");
  userText.classList.add("text");
  userText.innerHTML = message;

  usermessage.appendChild(userAvatar);
  usermessage.appendChild(userText);
  chat.appendChild(usermessage);
  chat.scrollTop = chat.scrollHeight;
}

function displayBotMessage(message) {
let chat = document.getElementById("chat");

let botMessage = document.createElement("div");
botMessage.classList.add("message");
botMessage.classList.add("bot");

let botAvatar = document.createElement("div");
botAvatar.classList.add("avatar");

let botText = document.createElement("div");
botText.classList.add("text");
botText.innerHTML = message;

botMessage.appendChild(botAvatar);
botMessage.appendChild(botText);
chat.appendChild(botMessage);
chat.scrollTop = chat.scrollHeight;
}


// document.getElementById("send").addEventListener("click", sendMessage);


// Get modal elements
const modal = document.getElementById("imageModal");
const cameraButton = document.getElementById("camera");
const closeModal = document.getElementById("closeModal");

// Open modal
cameraButton.addEventListener("click", function () {
  modal.style.display = "flex";
  document.body.classList.add("modal-open"); // Apply blur effect
});

// Close modal
closeModal.addEventListener("click", function () {
  modal.style.display = "none";
  document.body.classList.remove("modal-open"); // Remove blur effect
});

// Close modal when clicking outside content
window.addEventListener("click", function (event) {
  if (event.target === modal) {
      modal.style.display = "none";
      document.body.classList.remove("modal-open");
  }
});

function typeEffect(element, text, speed = 50) {
let i = 0;
element.innerHTML = ""; // Clear previous text before typing

function type() {
    if (i < text.length) {
        element.innerHTML += text.charAt(i);
        i++;
        setTimeout(type, speed);
    }
}

type();
}

// Call function when the page loads
document.addEventListener("DOMContentLoaded", function () {
const botTextElement = document.getElementById("bot-text"); // Make sure your bot message has this ID
const message = `Welcome to SkinCare AI! 🌿✨ I'm here to help you analyze your skin condition and provide insights about potential allergies or issues. Simply upload an image and answer a few questions, and I'll guide you toward understanding your skin better. Let's get started! 😊`;

typeEffect(botTextElement, message, 30); // Adjust speed as needed
});

// const image_input = document.querySelector("#image_input");
// var uploaded_image=" ";
// image_input.addEventListener("change", function(){
//     const reader = new FileReader();
//     reader.addEventListener("load", ()=>{
//         uploaded_image = reader.result;
//         document.querySelector("#display-image").style.backgroundImage = `url(${uploaded_image})`
//     });
//     reader.readAsDataURL(this.files[0])
// })

// -------------- BACKENT INTEGRATION -----------------


const INPUT = document.getElementById("input")
const SEND = document.getElementById("send");

const sendMessage = async (user_input)=>{
  try {
      const response = await fetch("http://localhost:5000/send-message", {
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
      alert("Something went wrong!")
  }
}

SEND.addEventListener("click", ()=>{
  sendMessage(INPUT.value);
  
  displayUserMessage(INPUT.value);
  INPUT.value = "";
})

