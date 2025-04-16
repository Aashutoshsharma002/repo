const express = require("express")
const app = express()
const cors = require("cors")
require("dotenv").config()
const connectDB = require("./config/db")
const PORT = process.env.PORT || 5000

// Global CORS configuration to allow everything
app.use(cors({
  origin: "*", // Allow all origins
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"], // Allow common methods
  allowedHeaders: ["Content-Type", "Authorization"] // Allow common headers
}))

// Other middlewares
app.use(express.json())
app.use(express.urlencoded({ extended: false }))
app.use(express.static("public"))

// connect to the mongodb database
// connectDB()

// Routes
app.use('/api/items', require("./routes/items"))
app.use('/api/payment', require("./routes/payment"))

app.listen(PORT, () => console.log("Server is running on port", PORT))
