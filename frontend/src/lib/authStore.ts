type OnRefreshedCallback = (newToken: string) => void
type OnLogoutCallback = () => void

let _accessToken: string | null = null
let _onRefreshed: OnRefreshedCallback | null = null
let _onLogout: OnLogoutCallback | null = null

export const authStore = {
  getAccessToken(): string | null {
    return _accessToken
  },
  setAccessToken(token: string | null) {
    _accessToken = token
  },
  onRefreshed(cb: OnRefreshedCallback | null) {
    _onRefreshed = cb
  },
  notifyRefreshed(token: string) {
    _onRefreshed?.(token)
  },
  onLogout(cb: OnLogoutCallback | null) {
    _onLogout = cb
  },
  notifyLogout() {
    _onLogout?.()
  },
}
