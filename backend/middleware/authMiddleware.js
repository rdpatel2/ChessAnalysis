const jwt = require("jsonwebtoken");

const authMiddleware = (req, res, next) => {
  const token = req.header("Authorization");

  if (!token) {
    return res
      .status(401)
      .json({ message: "Access denied. No token provided." });
  }

  try {
    // Verify the token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Attach the user information to the request object
    req.user = decoded;

    // Proceed to the next middleware or route
    next();
  } catch (error) {
    console.error(error);
    res.status(400).json({ message: "Invalid token." });
  }
};

module.exports = authMiddleware;
