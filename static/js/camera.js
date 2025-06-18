// Camera and Palm Scanning Utilities
class PalmScanner {
    constructor() {
        this.stream = null;
        this.isScanning = false;
    }

    async startCamera(videoElement) {
        try {
            // Stop any existing stream
            this.stopCamera();

            // Get user media with video constraints
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            videoElement.srcObject = this.stream;
            
            return true;
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.handleCameraError(error);
            return false;
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => {
                track.stop();
            });
            this.stream = null;
        }
    }

    captureImage(videoElement, canvasElement) {
        if (!videoElement || !canvasElement) {
            console.error('Video or canvas element not found');
            return null;
        }

        const canvas = canvasElement;
        const ctx = canvas.getContext('2d');
        
        // Set canvas size to match video
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        
        // Draw current video frame to canvas
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        
        return canvas;
    }

    async captureBlob(videoElement, canvasElement, quality = 0.8) {
        const canvas = this.captureImage(videoElement, canvasElement);
        if (!canvas) return null;

        return new Promise((resolve) => {
            canvas.toBlob((blob) => {
                resolve(blob);
            }, 'image/png', quality);
        });
    }

    handleCameraError(error) {
        let message = 'Unable to access camera. ';
        
        switch (error.name) {
            case 'NotAllowedError':
                message += 'Please allow camera access and try again.';
                break;
            case 'NotFoundError':
                message += 'No camera found on this device.';
                break;
            case 'NotSupportedError':
                message += 'Camera is not supported in this browser.';
                break;
            case 'NotReadableError':
                message += 'Camera is already in use by another application.';
                break;
            default:
                message += 'Please check your camera and try again.';
        }
        
        this.showError(message);
    }

    showError(message) {
        // Create and show error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
    }

    showSuccess(message) {
        // Create and show success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
        alertDiv.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
    }

    async submitPalmImage(endpoint, formData, onSuccess, onError) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                if (onSuccess) onSuccess(data);
            } else {
                if (onError) onError(data.message || 'Operation failed');
            }
        } catch (error) {
            console.error('Error submitting palm image:', error);
            if (onError) onError('Network error occurred. Please try again.');
        }
    }

    validateImageQuality(canvas) {
        // Basic image quality validation
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // Check if image is too dark or too bright
        let totalBrightness = 0;
        for (let i = 0; i < data.length; i += 4) {
            const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
            totalBrightness += brightness;
        }
        
        const avgBrightness = totalBrightness / (data.length / 4);
        
        if (avgBrightness < 50) {
            return { valid: false, message: 'Image is too dark. Please ensure good lighting.' };
        }
        
        if (avgBrightness > 200) {
            return { valid: false, message: 'Image is too bright. Please adjust lighting.' };
        }
        
        return { valid: true, message: 'Image quality is good.' };
    }
}

// Global palm scanner instance
const palmScanner = new PalmScanner();

// Utility functions for form handling
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

function showLoading(element) {
    element.disabled = true;
    element.classList.add('loading');
    
    const originalText = element.innerHTML;
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Processing...
    `;
    
    return originalText;
}

function hideLoading(element, originalText) {
    element.disabled = false;
    element.classList.remove('loading');
    element.innerHTML = originalText;
}

// Check for camera support
function checkCameraSupport() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        palmScanner.showError('Camera is not supported in this browser. Please use a modern browser with camera support.');
        return false;
    }
    return true;
}

// Initialize camera check on page load
document.addEventListener('DOMContentLoaded', function() {
    checkCameraSupport();
});

// Cleanup function for page unload
window.addEventListener('beforeunload', function() {
    palmScanner.stopCamera();
});
