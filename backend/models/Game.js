import mongoose from "mongoose";
const { Schema } = mongoose;

// Define Game Schema
const gameSchema = new Schema({
  moves: [String], // Array of move strings in SAN (e.g., ["e4", "e5"])
  analysis: [String], // Array of analysis strings (e.g., ["best move: e4", "best move: e5"])
});

const Game = mongoose.model("Game", gameSchema);

export default { Game };
