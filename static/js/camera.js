document.addEventListener('alpine:init', () => {
  Alpine.data('answerCard', (initialStatus, hasSavedPhoto) => ({
    status: initialStatus || '',
    hasSavedPhoto: Boolean(hasSavedPhoto),
    previewUrl: null,

    get needsPhoto() {
      return this.status === 'NO_CONFORME';
    },
    get showPhotoInput() {
      return this.status === 'NO_CONFORME' || this.status === 'PARCIAL';
    },
    get hasPhoto() {
      return this.hasSavedPhoto || Boolean(this.previewUrl);
    },
    get canSubmit() {
      return this.status !== '' && (!this.needsPhoto || this.hasPhoto);
    },

    onFileSelected(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.previewUrl = URL.createObjectURL(file);
      this.hasSavedPhoto = false;
    },

    retake() {
      this.previewUrl = null;
      this.$refs.fileInput.value = '';
      this.$refs.fileInput.click();
    },
  }));
});
