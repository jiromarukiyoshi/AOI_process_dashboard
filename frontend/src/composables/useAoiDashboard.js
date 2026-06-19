import { computed, onMounted, ref } from "vue"
import axios from "../axios"
import { buildMockPayload, mockDates } from "../mockData"


export function useAoiDashboard() {
  const dates = ref([])
  const selectedDate = ref("")
  const payload = ref(buildMockPayload())
  const loading = ref(false)
  const error = ref("")
  const usingMock = ref(false)

  const hasRows = computed(() => payload.value.rows.length > 0)

  async function loadDates() {
    try {
      const response = await axios.get("/api/aoi-dashboard/shipment-dates/")
      dates.value = response.data
      usingMock.value = false
    } catch (exc) {
      dates.value = mockDates
      usingMock.value = true
    }

    if (!selectedDate.value) {
      selectedDate.value = formatLocalDate(new Date())
    }
  }

  async function loadDashboard() {
    loading.value = true
    error.value = ""
    try {
      const response = await axios.get("/api/aoi-dashboard/", {
        params: { ship_date: selectedDate.value },
      })
      payload.value = response.data
      usingMock.value = false
    } catch (exc) {
      payload.value = buildMockPayload(selectedDate.value)
      usingMock.value = true
      error.value = "APIに接続できないためデモデータを表示しています。"
    } finally {
      loading.value = false
    }
  }

  async function initialize() {
    await loadDates()
    await loadDashboard()
  }

  onMounted(initialize)

  return {
    dates,
    selectedDate,
    payload,
    loading,
    error,
    usingMock,
    hasRows,
    loadDashboard,
  }
}

function formatLocalDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return year + "-" + month + "-" + day
}
