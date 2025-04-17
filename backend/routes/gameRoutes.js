import express from "express";
import { getGames, postGame } from "../controllers/gameController.js";

const router = express.Router();

router.get("/", getGames);
router.post("/", postGame);

export default router;
