import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import User from "../models/User.js";
import express from "express";

const router = express.Router();

export const registerUser = async (req, res) => {
  try {
    const { username, password } = req.body;

    const userExists = await User.findOne({ username });
    if (!userExists) {
      const hashedPassword = await bcrypt.hash(password, 12);
      const newUser = new User({
        username,
        password: hashedPassword,
        games: [],
      });
      await newUser.save();
      res.status(201).send("User created");
    } else {
      res.status(400).send("User already exists");
    }
  } catch (error) {
    console.error(error);
    res.status(500).send("Server error");
  }
};

export const loginUser = async (req, res) => {
  try {
    const { username, password } = req.body;
    const user = await User.findOne({ username });
    if (user && (await bcrypt.compare(password, user.password))) {
      const token = jwt.sign(
        { username: user.username, id: user._id },
        process.env.JWT_SECRET,
        { expiresIn: "1h" }
      );
      res.status(200).json({ user: user.username, token });
    } else {
      res.status(400).send("Invalid credentials");
    }
  } catch (error) {
    console.error(error);
    res.status(500).send("Server error");
  }
};
