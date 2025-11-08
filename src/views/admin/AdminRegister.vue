<template>
  <AdminAuthTabs default-tab="register" />
</template>

<script>
import AdminAuthTabs from './AdminLogin.vue'

export default {
  name: 'AdminRegister',
  components: {
    AdminAuthTabs
  }
}
</script>
