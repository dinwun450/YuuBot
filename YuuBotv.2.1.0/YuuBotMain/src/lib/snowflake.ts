import * as snowflake from 'snowflake-sdk'

type Row = Record<string, unknown>
type SnowflakeBindValue = string | number | boolean | null

type SnowflakeSchema = 'GLOBAL' | 'JP'

function getConnection(schema?: SnowflakeSchema) {
  const connection = snowflake.createConnection({
    account: process.env.SNOWFLAKE_ACCOUNT,
    username: process.env.SNOWFLAKE_USER,
    password: process.env.SNOWFLAKE_PASSWORD,
    warehouse: process.env.SNOWFLAKE_WAREHOUSE,
    database: process.env.SNOWFLAKE_DATABASE,
    schema: schema ?? (process.env.SNOWFLAKE_SCHEMA as SnowflakeSchema | undefined),
  })

  return connection
}

export async function executeQuery(
  sql: string,
  binds: SnowflakeBindValue[] = [],
  schema?: SnowflakeSchema,
): Promise<Row[]> {
  const conn = getConnection(schema)

  return new Promise<Row[]>((resolve, reject) => {
    conn.connect((err, connection) => {
      if (err) return reject(err)

      connection.execute({
        sqlText: sql,
        binds,
        complete: (err2, _stmt, rows) => {
          try {
            connection.destroy()
          } catch {
            // ignore
          }

          if (err2) return reject(err2)
          resolve(rows || [])
        },
      })
    })
  })
}

export async function testConnection(): Promise<boolean> {
  try {
    const rows = await executeQuery('SELECT 1')
    return Array.isArray(rows)
  } catch {
    return false
  }
}

export type { SnowflakeSchema }
