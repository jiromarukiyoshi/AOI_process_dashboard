import axios from "axios"


axios.defaults.withCredentials = true
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || ""

function getCookie(name) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop().split(";").shift()
  return null
}

axios.interceptors.request.use((config) => {
  const csrftoken = getCookie("csrftoken")
  if (csrftoken) {
    config.headers["X-CSRFToken"] = csrftoken
  }
  return config
})

export default axios
