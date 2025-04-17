import mongoose from "mongoose";
const { Schema } = mongoose;

// Define User Schema
const userSchema = new Schema({
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true }, // Store hashed password
  games: [{ type: Schema.Types.ObjectId, ref: "Game" }], // Array of up to 10 games
});

// Create Models
const User = mongoose.model("User", userSchema);

export default { User };
