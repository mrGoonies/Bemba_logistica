document.addEventListener('alpine:init', () => {
  Alpine.data('answerCard', (initialStatus, hasSavedPhoto) => ({
    status: initialStatus || '',
    hasSavedPhoto: Boolean(hasSavedPhoto),
    stream: null,
    cameraActive: false,
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
        this.cameraActive = true;
        this.$nextTick(() => {
          this.$refs.video.srcObject = this.stream;
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
    },

    capture() {
      const video = this.$refs.video;
      const canvas = this.$refs.canvas;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      canvas.toBlob(
        (blob) => {
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
