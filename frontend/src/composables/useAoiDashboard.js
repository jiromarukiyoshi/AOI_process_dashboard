import { computed, onMounted, onUnmounted, ref } from "vue"
import axios from "../axios"
import { buildMockPayload, buildMockSerialPayload, mockDates } from "../mockData"


const SHIPMENT_DATE_STORAGE_KEY = "aoi-dashboard-shipment-date"
const SHIPMENT_DATE_SAVED_ON_KEY = "aoi-dashboard-shipment-date-saved-on"
const AUTO_REFRESH_INTERVAL_MS = 5 * 60 * 1000


export function useAoiDashboard() {
  const dates = ref([])
  const selectedDate = ref("")
  const payload = ref(buildMockPayload())
  const serialPayload = ref(buildMockSerialPayload())
  const loading = ref(false)
  const error = ref("")
  const usingMock = ref(false)
  const lastUpdatedAt = ref("")
  let autoRefreshTimer = null

  const hasRows = computed(() => payload.value.rows.length > 0)
  const hasSerialRows = computed(() => serialPayload.value.rows.length > 0)

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
      selectedDate.value = getStoredShipmentDate() || formatLocalDate(new Date())
    }
  }

  async function loadDashboard() {
    storeShipmentDate(selectedDate.value)
    loading.value = true
    error.value = ""
    try {
      const [dashboardResponse, serialResponse] = await Promise.all([
        axios.get("/api/aoi-dashboard/", {
          params: { ship_date: selectedDate.value },
        }),
        axios.get("/api/aoi-dashboard/serials/", {
          params: { ship_date: selectedDate.value },
        }),
      ])
      payload.value = dashboardResponse.data
      serialPayload.value = serialResponse.data
      usingMock.value = false
    } catch (exc) {
      payload.value = buildMockPayload(selectedDate.value)
      serialPayload.value = buildMockSerialPayload(selectedDate.value)
      usingMock.value = true
      error.value = "APIに接続できないためデモデータを表示しています。"
    } finally {
      lastUpdatedAt.value = formatLocalDateTime(new Date())
      loading.value = false
    }
  }

  async function initialize() {
    await loadDates()
    await loadDashboard()
    startAutoRefresh()
  }

  function startAutoRefresh() {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer)
    autoRefreshTimer = setInterval(() => {
      if (!loading.value) loadDashboard()
    }, AUTO_REFRESH_INTERVAL_MS)
  }

  onMounted(initialize)
  onUnmounted(() => {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer)
  })

  return {
    dates,
    selectedDate,
    payload,
    serialPayload,
    loading,
    error,
    usingMock,
    lastUpdatedAt,
    hasRows,
    hasSerialRows,
    loadDashboard,
  }
}

function formatLocalDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return year + "-" + month + "-" + day
}

function formatLocalDateTime(date) {
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")
  const seconds = String(date.getSeconds()).padStart(2, "0")
  return formatLocalDate(date) + " " + hours + ":" + minutes + ":" + seconds
}

function getStoredShipmentDate() {
  try {
    const value = localStorage.getItem(SHIPMENT_DATE_STORAGE_KEY)
    const savedOn = localStorage.getItem(SHIPMENT_DATE_SAVED_ON_KEY)
    const today = formatLocalDate(new Date())
    if (savedOn !== today) return ""
    return /^\d{4}-\d{2}-\d{2}$/.test(value || "") ? value : ""
  } catch {
    return ""
  }
}

function storeShipmentDate(value) {
  if (!value) return
  try {
    localStorage.setItem(SHIPMENT_DATE_STORAGE_KEY, value)
    localStorage.setItem(SHIPMENT_DATE_SAVED_ON_KEY, formatLocalDate(new Date()))
  } catch {
    // Continue without persistence when browser storage is unavailable.
  }
}