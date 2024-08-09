document.addEventListener('DOMContentLoaded', () => {
    const summarizeForm = document.getElementById('summarize-text-form');
    const summaryResult = document.getElementById('summary-result');

    summarizeForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const text = document.getElementById('text').value.trim();

        if (!text) {
            summaryResult.textContent = 'Text cannot be empty.';
            return;
        }

        try {
            const response = await fetch('/summarize-text/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await response.json();
            summaryResult.textContent = data['summary-result'] || data.error;
        } catch (error) {
            summaryResult.textContent = 'An unexpected error occurred.';
            console.error('Error:', error);
        }
    });

    const generateImageForm = document.getElementById('generate-image-form');
    const generatedImage = document.getElementById('generated-image');

    generateImageForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const prompt = document.getElementById('prompt').value.trim();

        if (!prompt) {
            alert('Prompt cannot be empty.');
            return;
        }

        try {
            const response = await fetch('/generate-image/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });
            const data = await response.json();

            if (data.image_url) {
                generatedImage.src = data.image_url;
                generatedImage.style.display = 'block';
            } else {
                generatedImage.style.display = 'none';
                alert(data.error);
            }
        } catch (error) {
            alert('An unexpected error occurred.');
            console.error('Error:', error);
        }
    });

    const uploadFileForm = document.getElementById('upload-file-form');
    const fileText = document.getElementById('file-text');

    uploadFileForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const fileInput = document.getElementById('file').files[0];

        if (!fileInput) {
            fileText.textContent = 'No file selected.';
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput);

        try {
            const response = await fetch('/upload-file/', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.text) {
                fileText.innerHTML = `
                    <strong>Extracted Text:</strong><br>${data.text}<br>
                    <strong>Summary:</strong><br>${data.summary}
                `;
            } else {
                fileText.textContent = data.error;
            }
        } catch (error) {
            fileText.textContent = 'An unexpected error occurred.';
            console.error('Error:', error);
        }
    });


    function displayError(message) {
        videoLink.innerHTML = `<p>Error: ${message}</p>`;
    }

    function openTab(evt, tabName) {
        const tabContent = document.getElementsByClassName("tab-content");
        Array.from(tabContent).forEach(content => content.style.display = "none");

        const tabLinks = document.getElementsByClassName("tab-link");
        Array.from(tabLinks).forEach(link => link.classList.remove("active"));

        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.classList.add("active");
    }

    // Set the default tab to open
    document.querySelector('.tab-link').click();
});

document.getElementById('generate-text-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const textprompt = document.getElementById('textprompt').value;
    const loadingIndicator = document.getElementById('loading-indicator');
    const generatedText = document.getElementById('generated-text');
    const videoContainer = document.getElementById('video-container');
    
    loadingIndicator.style.display = 'block';
    generatedText.innerHTML = '';
    videoContainer.style.display = 'none';

    fetch('/generate-text/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')  // Make sure to include CSRF token
        },
        body: JSON.stringify({textprompt: textprompt})
    })
    .then(response => response.json())
    .then(data => {
        loadingIndicator.style.display = 'none';
        if (data.error) {
            generatedText.innerHTML = `Error: ${data.error}`;
        } else {
            generatedText.innerHTML = data.generated_text;
            document.getElementById('video-source').src = data.final_video_path;
            videoContainer.style.display = 'block';
        }
    })
    .catch(error => {
        loadingIndicator.style.display = 'none';
        generatedText.innerHTML = `Error: ${error}`;
    });
});

// Function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

