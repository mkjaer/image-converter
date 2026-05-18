const uploadBox = document.getElementById("uploadBox");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");

uploadBox.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    fileName.textContent = fileInput.files[0].name;
  }
});

uploadBox.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadBox.classList.add("dragover");
});

uploadBox.addEventListener("dragleave", () => {
  uploadBox.classList.remove("dragover");
});

uploadBox.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadBox.classList.remove("dragover");

  if (event.dataTransfer.files.length > 0) {
    fileInput.files = event.dataTransfer.files;
    fileName.textContent = event.dataTransfer.files[0].name;
  }
});
