declare module 'snowflake-sdk' {
  export type SnowflakeBindValue = string | number | boolean | null

  export interface SnowflakeConnectionOptions {
    account?: string
    username?: string
    password?: string
    warehouse?: string
    database?: string
    schema?: string
  }

  export interface SnowflakeConnection {
    connect(callback: (err: Error | null, connection: SnowflakeConnection) => void): void
    execute(options: {
      sqlText: string
      binds?: SnowflakeBindValue[]
      complete: (err: Error | null, stmt: unknown, rows: Record<string, unknown>[]) => void
    }): void
    destroy(): void
  }

  export function createConnection(options: SnowflakeConnectionOptions): SnowflakeConnection
}
