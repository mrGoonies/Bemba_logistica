document.addEventListener('alpine:init', () => {
  Alpine.data('answerCard', (initialStatus, hasSavedPhoto) => ({
    status: initialStatus || '',
    hasSavedPhoto: Boolean(hasSavedPhoto),
    stream: null,
    cameraActive: false,
    videoReady: false,
    capturedPreviewUrl: null,

    get needsPhoto() {
      return this.status === 'NO_CONFORME';
    },
    get showCamera() {
      return this.status === 'NO_CONFORME' || this.status === 'PARCIAL';
    },
    get hasPhoto() {
      return this.hasSavedPhoto || Boolean(this.capturedPreviewUrl);
    },
    get canSubmit() {
      return this.status !== '' && (!this.needsPhoto || this.hasPhoto);
    },

    onStatusChange() {
      if (!this.showCamera) {
        this.stopCamera();
      }
    },

    async startCamera() {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
          audio: false,
        });
        this.videoReady = false;
        this.cameraActive = true;
        this.$nextTick(() => {
          const video = this.$refs.video;
          video.srcObject = this.stream;
          video.onloadedmetadata = () => {
            video.play().catch(() => {});
            this.videoReady = true;
          };
        });
      } catch (err) {
        alert('No se pudo acceder a la cámara. Verifica los permisos del navegador.');
      }
    },

    stopCamera() {
      if (this.stream) {
        this.stream.getTracks().forEach((track) => track.stop());
        this.stream = null;
      }
      this.cameraActive = false;
      this.videoReady = false;
    },

    capture() {
      const video = this.$refs.video;
      if (!this.videoReady || !video.videoWidth || !video.videoHeight) {
        alert('La cámara todavía se está iniciando, espera un segundo e intenta de nuevo.');
        return;
      }
      const canvas = this.$refs.canvas;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            alert('No se pudo capturar la fotografía. Intenta nuevamente.');
            return;
          }
          const file = new File([blob], `foto_${Date.now()}.jpg`, { type: 'image/jpeg' });
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          this.$refs.fileInput.files = dataTransfer.files;
          this.capturedPreviewUrl = URL.createObjectURL(blob);
          this.hasSavedPhoto = false;
          this.stopCamera();
        },
        'image/jpeg',
        0.85
      );
    },

    retake() {
      this.capturedPreviewUrl = null;
      this.$refs.fileInput.value = '';
      this.startCamera();
    },
  }));
});
