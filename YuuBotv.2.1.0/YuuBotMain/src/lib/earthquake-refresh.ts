import { executeQuery, type SnowflakeSchema } from './snowflake'

type JapaneseEarthquakeRow = {
  date: string | null
  time: string | null
  location: string | null
  magnitude: number | null
  intensity: string | null
  latitude: number | null
  longitude: number | null
}

type GlobalEarthquakeRow = {
  date: string | null
  time: string | null
  magnitude: number | null
  location: string | null
  title: string | null
  tsunami: boolean | null
  latitude: number | null
  longitude: number | null
}

type UsgsEarthquakeFeature = {
  properties?: {
    mag?: number | null
    time?: number | null
    place?: string | null
    title?: string | null
    tsunami?: number | boolean | null
  }
  geometry?: {
    coordinates?: Array<number | null>
  }
}

const YAHOO_EARTHQUAKE_LIST_URL = 'https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/'
const USGS_ALL_WEEK_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson'

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function stripTags(value: string) {
  return value.replace(/<[^>]*>/g, ' ')
}

function normalizeText(value: string) {
  return stripTags(value).replace(/\s+/g, ' ').trim()
}

function extractLabelValue(html: string, label: string) {
  const pattern = new RegExp(
    `<small>${escapeRegExp(label)}</small>[\\s\\S]*?<td[^>]*>[\\s\\S]*?<small>([\\s\\S]*?)</small>`,
    'i',
  )
  const match = html.match(pattern)
  return match ? normalizeText(match[1]) : null
}

function formatDateTimeParts(year: string, month: string, day: string, hour: string, minute: string) {
  return {
    date: `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`,
    time: `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}:00`,
  }
}

function convertTimestampToDate(timestamp: number) {
  const normalizedTimestamp = timestamp > 1e10 ? Math.floor(timestamp / 1000) : timestamp
  const date = new Date(normalizedTimestamp * 1000)

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')

  return {
    date: `${year}-${month}-${day}`,
    time: `${hour}:${minute}:${second}`,
  }
}

async function fetchYahooEarthquakeDetailLinks() {
  const response = await fetch(YAHOO_EARTHQUAKE_LIST_URL, { cache: 'no-store' })

  if (!response.ok) {
    throw new Error(`Yahoo earthquake list failed: ${response.status}`)
  }

  const html = await response.text()
  const links = new Set<string>()
  const linkPattern = /href="(\/weather\/jp\/earthquake\/\d{14}\.html)"/g

  for (const match of html.matchAll(linkPattern)) {
    links.add(match[1])
  }

  return Array.from(links)
}

function parseJapaneseEarthquakeDetail(html: string): JapaneseEarthquakeRow {
  const rawDateTime = extractLabelValue(html, '発生時刻')
  const location = extractLabelValue(html, '震源地')
  const magnitudeText = extractLabelValue(html, 'マグニチュード')
  const intensityText = extractLabelValue(html, '最大震度')
  const coordsMatch = html.match(/北緯\s*([0-9.]+)度\s*\/\s*東経\s*([0-9.]+)度/)

  let date: string | null = null
  let time: string | null = null

  if (rawDateTime) {
    const dateTimeMatch = rawDateTime.match(/(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2})時(\d{1,2})分/)

    if (dateTimeMatch) {
      const parts = formatDateTimeParts(
        dateTimeMatch[1],
        dateTimeMatch[2],
        dateTimeMatch[3],
        dateTimeMatch[4],
        dateTimeMatch[5],
      )
      date = parts.date
      time = parts.time
    }
  }

  return {
    date,
    time,
    location,
    magnitude: magnitudeText ? Number.parseFloat(magnitudeText) : null,
    intensity: intensityText,
    latitude: coordsMatch ? Number.parseFloat(coordsMatch[1]) : null,
    longitude: coordsMatch ? Number.parseFloat(coordsMatch[2]) : null,
  }
}

async function fetchJapaneseEarthquakeRows() {
  const links = await fetchYahooEarthquakeDetailLinks()
  const rows = await Promise.all(
    links.map(async (link) => {
      const response = await fetch(`https://typhoon.yahoo.co.jp${link}`, { cache: 'no-store' })

      if (!response.ok) {
        throw new Error(`Yahoo earthquake detail failed: ${response.status}`)
      }

      const html = await response.text()
      return parseJapaneseEarthquakeDetail(html)
    }),
  )

  return rows.filter((row) => row.date && row.time)
}

async function fetchGlobalEarthquakeRows() {
  const response = await fetch(USGS_ALL_WEEK_URL, {
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/geo+json',
    },
  })

  if (!response.ok) {
    throw new Error(`USGS earthquake feed failed: ${response.status}`)
  }

  const quakeData = await response.json()
  const features = Array.isArray(quakeData?.features) ? quakeData.features : []

  return features
    .map((quake: UsgsEarthquakeFeature) => {
      const magnitude = quake?.properties?.mag

      if (magnitude === null || magnitude === undefined || magnitude < 2.0) {
        return null
      }

      const time = quake?.properties?.time
      const coordinates = Array.isArray(quake?.geometry?.coordinates) ? quake.geometry.coordinates : []
      const converted = typeof time === 'number' ? convertTimestampToDate(time) : { date: null, time: null }

      const row: GlobalEarthquakeRow = {
        date: converted.date,
        time: converted.time,
        magnitude: magnitude ?? null,
        location: quake?.properties?.place ?? null,
        title: quake?.properties?.title ?? null,
        tsunami: quake?.properties?.tsunami === 0 ? false : Boolean(quake?.properties?.tsunami),
        latitude: coordinates.length > 1 ? coordinates[1] : null,
        longitude: coordinates.length > 0 ? coordinates[0] : null,
      }

      return row
    })
    .filter((row): row is GlobalEarthquakeRow => Boolean(row && row.date && row.time))
}

async function insertRows(
  schema: SnowflakeSchema,
  tableName: string,
  columns: string[],
  rows: Array<Array<string | number | boolean | null>>,
) {
  if (rows.length === 0) {
    return
  }

  const placeholders = rows.map(() => `(${columns.map(() => '?').join(', ')})`).join(', ')
  const sql = `INSERT INTO ${tableName} (${columns.join(', ')}) VALUES ${placeholders}`
  const binds = rows.flat()

  await executeQuery(sql, binds, schema)
}

async function resetJapaneseOverallTable(schema: SnowflakeSchema) {
  await executeQuery(
    `CREATE OR REPLACE TABLE all_jp_earthquakes (
      date STRING,
      time STRING,
      epicenter STRING,
      magnitude FLOAT,
      intensity STRING,
      lat FLOAT,
      lon FLOAT
    )`,
    [],
    schema,
  )
}

async function resetJapaneseCoordinateTable(schema: SnowflakeSchema) {
  await executeQuery(
    `CREATE OR REPLACE TABLE jp_earthquakes_coords (
      lat FLOAT,
      lon FLOAT
    )`,
    [],
    schema,
  )
}

async function resetGlobalOverallTable(schema: SnowflakeSchema) {
  await executeQuery(
    `CREATE OR REPLACE TABLE all_earthquakes_week (
      date STRING,
      time STRING,
      magnitude FLOAT,
      location STRING,
      title STRING,
      tsunami BOOLEAN,
      lat FLOAT,
      lon FLOAT
    )`,
    [],
    schema,
  )
}

async function resetGlobalCoordinateTable(schema: SnowflakeSchema) {
  await executeQuery(
    `CREATE OR REPLACE TABLE all_earthquakes_week_coords (
      lat FLOAT,
      lon FLOAT
    )`,
    [],
    schema,
  )
}

export async function refreshJapaneseOverallEarthquakes(schema: SnowflakeSchema) {
  const rows = await fetchJapaneseEarthquakeRows()

  await resetJapaneseOverallTable(schema)
  await insertRows(
    schema,
    'all_jp_earthquakes',
    ['date', 'time', 'epicenter', 'magnitude', 'intensity', 'lat', 'lon'],
    rows.map((row) => [
      row.date,
      row.time,
      row.location,
      row.magnitude,
      row.intensity,
      row.latitude,
      row.longitude,
    ]),
  )

  return { inserted: rows.length }
}

export async function refreshJapaneseCoordinateEarthquakes(schema: SnowflakeSchema) {
  const rows = await fetchJapaneseEarthquakeRows()

  await resetJapaneseCoordinateTable(schema)
  await insertRows(
    schema,
    'jp_earthquakes_coords',
    ['lat', 'lon'],
    rows.map((row) => [row.latitude, row.longitude]),
  )

  return { inserted: rows.length }
}

export async function refreshGlobalOverallEarthquakes(schema: SnowflakeSchema) {
  const rows = await fetchGlobalEarthquakeRows()

  await resetGlobalOverallTable(schema)
  await insertRows(
    schema,
    'all_earthquakes_week',
    ['date', 'time', 'magnitude', 'location', 'title', 'tsunami', 'lat', 'lon'],
    rows.map((row) => [
      row.date,
      row.time,
      row.magnitude,
      row.location,
      row.title,
      row.tsunami,
      row.latitude,
      row.longitude,
    ]),
  )

  return { inserted: rows.length }
}

export async function refreshGlobalCoordinateEarthquakes(schema: SnowflakeSchema) {
  const rows = await fetchGlobalEarthquakeRows()

  await resetGlobalCoordinateTable(schema)
  await insertRows(
    schema,
    'all_earthquakes_week_coords',
    ['lat', 'lon'],
    rows.map((row) => [row.latitude, row.longitude]),
  )

  return { inserted: rows.length }
}