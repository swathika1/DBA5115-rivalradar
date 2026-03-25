import { createContext, useContext, useState, useCallback } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)

  const signup = useCallback(async (data) => {
    const res = await axios.post('/auth/signup', data)
    setToken(res.data.access_token)
    return res.data
  }, [])

  const login = useCallback(async ({ email, password }) => {
    const res = await axios.post('/auth/login', { email, password })
    setToken(res.data.access_token)
    return res.data
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  const authAxios = useCallback((config = {}) => {
    return axios({ ...config, headers: { ...(config.headers || {}), Authorization: `Bearer ${token}` } })
  }, [token])

  return (
    <AuthContext.Provider value={{ token, user, signup, login, logout, authAxios }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
