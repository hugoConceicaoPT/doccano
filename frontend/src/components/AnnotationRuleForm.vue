<template>
  <div class="annotation-rule-form">
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="name">Nome da Regra</label>
        <input id="name" v-model="form.name" type="text" class="form-control" required />
      </div>
      <div class="form-group">
        <label for="description">Descrição</label>
        <textarea
          id="description"
          v-model="form.description"
          class="form-control"
          required
        ></textarea>
      </div>
      // ... existing code ...
    </form>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        name: '',
        description: ''
        // ... existing code ...
      }
    }
  }
}
</script>
// ... existing code ...
