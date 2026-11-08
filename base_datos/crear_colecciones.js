var base = db.getSiblingDB("photobook_db");
var esquemas = {
  "usuarios": {
    "bsonType": "object",
    "required": [
      "_id",
      "activo",
      "nombreUsuario",
      "correo",
      "contrasena",
      "rol",
      "privacidad",
      "siguiendo",
      "seguidores",
      "creacionCuenta",
      "fechaActualizacion"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "activo": {
        "bsonType": "bool"
      },
      "nombreUsuario": {
        "bsonType": "string",
        "maxLength": 30,
        "minLength": 1,
        "pattern": "^[a-z0-9_]{3,30}$"
      },
      "correo": {
        "bsonType": "string",
        "maxLength": 120,
        "minLength": 1,
        "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
      },
      "contrasena": {
        "bsonType": "string",
        "maxLength": 255,
        "minLength": 1,
        "pattern": "^pbkdf2_sha256\\$"
      },
      "imagenPerfil": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 500
      },
      "biografia": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 255
      },
      "rol": {
        "bsonType": "string",
        "maxLength": 50,
        "minLength": 1
      },
      "privacidad": {
        "bsonType": "object",
        "required": [
          "perfilPublico",
          "correoVisible"
        ],
        "additionalProperties": false,
        "properties": {
          "perfilPublico": {
            "bsonType": "bool"
          },
          "correoVisible": {
            "bsonType": "bool"
          }
        }
      },
      "siguiendo": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "usuario",
            "inicioSeg"
          ],
          "additionalProperties": false,
          "properties": {
            "usuario": {
              "bsonType": "string",
              "maxLength": 30,
              "minLength": 1
            },
            "inicioSeg": {
              "bsonType": "date"
            }
          }
        }
      },
      "seguidores": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "usuario",
            "inicioSeg"
          ],
          "additionalProperties": false,
          "properties": {
            "usuario": {
              "bsonType": "string",
              "maxLength": 30,
              "minLength": 1
            },
            "inicioSeg": {
              "bsonType": "date"
            }
          }
        }
      },
      "creacionCuenta": {
        "bsonType": "date"
      },
      "fechaActualizacion": {
        "bsonType": "date"
      }
    }
  },
  "notificaciones": {
    "bsonType": "object",
    "required": [
      "_id",
      "usuarioNotificado",
      "tipo",
      "mensaje",
      "notificacionLeer",
      "fechaCreacion"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "usuarioNotificado": {
        "bsonType": "string",
        "maxLength": 30,
        "minLength": 1
      },
      "usuarioOrigen": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 30
      },
      "tipo": {
        "bsonType": "string",
        "maxLength": 15,
        "minLength": 1,
        "enum": [
          "seguir",
          "meGusta",
          "comentario",
          "mensaje",
          "sistema"
        ]
      },
      "mensaje": {
        "bsonType": "string",
        "maxLength": 255,
        "minLength": 1
      },
      "notificacionLeer": {
        "bsonType": "bool"
      },
      "fechaCreacion": {
        "bsonType": "date"
      }
    }
  },
  "publicaciones": {
    "bsonType": "object",
    "required": [
      "_id",
      "autor",
      "tipo",
      "archivoUrl",
      "formato",
      "tamanioBytes",
      "etiquetas",
      "categorias",
      "totalReacciones",
      "totalComentarios",
      "comentarios",
      "reacciones",
      "resoluciones",
      "estado",
      "fechaPublicacion",
      "historialEdiciones"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "autor": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "tipo": {
        "bsonType": "string",
        "maxLength": 10,
        "minLength": 1,
        "enum": [
          "imagen",
          "video"
        ]
      },
      "titulo": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 150
      },
      "descripcion": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 2000
      },
      "archivoUrl": {
        "bsonType": "string",
        "maxLength": 500,
        "minLength": 1
      },
      "formato": {
        "bsonType": "string",
        "maxLength": 5,
        "minLength": 1,
        "enum": [
          "jpg",
          "jpeg",
          "png",
          "gif",
          "mp4",
          "mov",
          "webm"
        ]
      },
      "tamanioBytes": {
        "bsonType": [
          "int",
          "long"
        ],
        "minimum": 1,
        "maximum": 9223372036854775807
      },
      "ancho": {
        "bsonType": [
          "int",
          "long",
          "null"
        ],
        "minimum": 1,
        "maximum": 2147483647
      },
      "alto": {
        "bsonType": [
          "int",
          "long",
          "null"
        ],
        "minimum": 1,
        "maximum": 2147483647
      },
      "duracionSegundos": {
        "bsonType": [
          "int",
          "long",
          "null"
        ],
        "minimum": 1,
        "maximum": 2147483647
      },
      "etiquetas": {
        "bsonType": "array",
        "items": {
          "bsonType": "string",
          "minLength": 1,
          "maxLength": 30
        },
        "maxItems": 30
      },
      "categorias": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "nombre",
            "slug"
          ],
          "additionalProperties": false,
          "properties": {
            "nombre": {
              "bsonType": "string",
              "maxLength": 60,
              "minLength": 1
            },
            "slug": {
              "bsonType": "string",
              "maxLength": 60,
              "minLength": 1
            }
          }
        }
      },
      "totalReacciones": {
        "bsonType": [
          "int",
          "long"
        ],
        "minimum": 0,
        "maximum": 2147483647
      },
      "totalComentarios": {
        "bsonType": [
          "int",
          "long"
        ],
        "minimum": 0,
        "maximum": 2147483647
      },
      "comentarios": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "autor",
            "contenido",
            "formato",
            "menciones",
            "archivosAdjuntos",
            "respuestas",
            "estado",
            "conteoReacciones",
            "fechaCreacion"
          ],
          "additionalProperties": false,
          "properties": {
            "autor": {
              "bsonType": "object",
              "required": [
                "nombreUsuario"
              ],
              "additionalProperties": false,
              "properties": {
                "nombreUsuario": {
                  "bsonType": "string",
                  "maxLength": 30,
                  "minLength": 1
                },
                "imagenPerfil": {
                  "bsonType": [
                    "string",
                    "null"
                  ],
                  "maxLength": 500
                }
              }
            },
            "contenido": {
              "bsonType": "string",
              "maxLength": 1000,
              "minLength": 1
            },
            "formato": {
              "bsonType": "string",
              "maxLength": 10,
              "minLength": 1
            },
            "menciones": {
              "bsonType": "array",
              "items": {
                "bsonType": "string"
              }
            },
            "archivosAdjuntos": {
              "bsonType": "array",
              "items": {
                "bsonType": "string"
              }
            },
            "respuestas": {
              "bsonType": "array",
              "items": {
                "bsonType": "object",
                "required": [
                  "autor",
                  "contenido",
                  "fechaCreacion"
                ],
                "additionalProperties": false,
                "properties": {
                  "autor": {
                    "bsonType": "object",
                    "required": [
                      "nombreUsuario"
                    ],
                    "additionalProperties": false,
                    "properties": {
                      "nombreUsuario": {
                        "bsonType": "string",
                        "maxLength": 30,
                        "minLength": 1
                      },
                      "imagenPerfil": {
                        "bsonType": [
                          "string",
                          "null"
                        ],
                        "maxLength": 500
                      }
                    }
                  },
                  "contenido": {
                    "bsonType": "string",
                    "maxLength": 1000,
                    "minLength": 1
                  },
                  "fechaCreacion": {
                    "bsonType": "date"
                  }
                }
              }
            },
            "estado": {
              "bsonType": "string",
              "maxLength": 10,
              "minLength": 1
            },
            "conteoReacciones": {
              "bsonType": "object",
              "required": [
                "meGusta",
                "amor",
                "aplauso",
                "sorpresa",
                "triste",
                "risa"
              ],
              "additionalProperties": false,
              "properties": {
                "meGusta": {
                  "bsonType": [
                    "int",
                    "long"
                  ],
                  "minimum": 0,
                  "maximum": 2147483647
                },
                "amor": {
                  "bsonType": [
                    "int",
                    "long"
                  ],
                  "minimum": 0,
                  "maximum": 2147483647
                },
                "aplauso": {
                  "bsonType": [
                    "int",
                    "long"
                  ],
                  "minimum": 0,
                  "maximum": 2147483647
                },
                "sorpresa": {
                  "bsonType": [
                    "int",
                    "long"
                  ],
                  "minimum": 0,
                  "maximum": 2147483647
                },
                "triste": {
                  "bsonType": [
                    "int",
                    "long"
                  ],
                  "minimum": 0,
                  "maximum": 2147483647
                },
                "risa": {
                  "bsonType": [
                    "int",
                    "long"
                  ],
                  "minimum": 0,
                  "maximum": 2147483647
                }
              }
            },
            "fechaCreacion": {
              "bsonType": "date"
            },
            "fechaEdicion": {
              "bsonType": [
                "date",
                "null"
              ]
            }
          }
        },
        "maxItems": 300
      },
      "reacciones": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "usuario",
            "tipoReaccion",
            "fecha"
          ],
          "additionalProperties": false,
          "properties": {
            "usuario": {
              "bsonType": "object",
              "required": [
                "nombreUsuario"
              ],
              "additionalProperties": false,
              "properties": {
                "nombreUsuario": {
                  "bsonType": "string",
                  "maxLength": 30,
                  "minLength": 1
                },
                "imagenPerfil": {
                  "bsonType": [
                    "string",
                    "null"
                  ],
                  "maxLength": 500
                }
              }
            },
            "tipoReaccion": {
              "bsonType": "string",
              "maxLength": 10,
              "minLength": 1,
              "enum": [
                "meGusta",
                "amor",
                "aplauso",
                "sorpresa",
                "triste",
                "risa"
              ]
            },
            "fecha": {
              "bsonType": "date"
            }
          }
        }
      },
      "resoluciones": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "calidad",
            "url"
          ],
          "additionalProperties": false,
          "properties": {
            "calidad": {
              "bsonType": "string",
              "maxLength": 10,
              "minLength": 1
            },
            "url": {
              "bsonType": "string",
              "maxLength": 500,
              "minLength": 1
            }
          }
        }
      },
      "estado": {
        "bsonType": "string",
        "maxLength": 10,
        "minLength": 1,
        "enum": [
          "publicado",
          "borrador",
          "eliminado"
        ]
      },
      "fechaPublicacion": {
        "bsonType": "date"
      },
      "historialEdiciones": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "tipoEdicion",
            "fecha"
          ],
          "additionalProperties": false,
          "properties": {
            "tipoEdicion": {
              "bsonType": "string",
              "maxLength": 20,
              "minLength": 1
            },
            "descripcion": {
              "bsonType": [
                "string",
                "null"
              ],
              "maxLength": 255
            },
            "fecha": {
              "bsonType": "date"
            }
          }
        },
        "maxItems": 100
      }
    }
  },
  "colecciones": {
    "bsonType": "object",
    "required": [
      "_id",
      "creador",
      "nombre",
      "tipo",
      "privacidad",
      "publicaciones",
      "colaboradores",
      "fechaCreacion"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "creador": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "nombre": {
        "bsonType": "string",
        "maxLength": 100,
        "minLength": 1
      },
      "descripcion": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 500
      },
      "tipo": {
        "bsonType": "string",
        "maxLength": 12,
        "minLength": 1,
        "enum": [
          "personal",
          "colaborativa"
        ]
      },
      "privacidad": {
        "bsonType": "string",
        "maxLength": 7,
        "minLength": 1,
        "enum": [
          "publica",
          "privada"
        ]
      },
      "portadaUrl": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 500
      },
      "publicaciones": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "orden",
            "tipo",
            "archivoUrl"
          ],
          "additionalProperties": false,
          "properties": {
            "orden": {
              "bsonType": [
                "int",
                "long"
              ],
              "minimum": 1,
              "maximum": 2147483647
            },
            "titulo": {
              "bsonType": [
                "string",
                "null"
              ],
              "maxLength": 150
            },
            "tipo": {
              "bsonType": "string",
              "maxLength": 10,
              "minLength": 1
            },
            "archivoUrl": {
              "bsonType": "string",
              "maxLength": 500,
              "minLength": 1
            }
          }
        }
      },
      "colaboradores": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "nombreUsuario"
          ],
          "additionalProperties": false,
          "properties": {
            "nombreUsuario": {
              "bsonType": "string",
              "maxLength": 30,
              "minLength": 1
            },
            "imagenPerfil": {
              "bsonType": [
                "string",
                "null"
              ],
              "maxLength": 500
            }
          }
        }
      },
      "fechaCreacion": {
        "bsonType": "date"
      }
    }
  },
  "categorias": {
    "bsonType": "object",
    "required": [
      "_id",
      "nombre",
      "slug",
      "subcategorias",
      "sinonimos",
      "totalPublicaciones"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "nombre": {
        "bsonType": "string",
        "maxLength": 60,
        "minLength": 1
      },
      "descripcion": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 300
      },
      "slug": {
        "bsonType": "string",
        "maxLength": 60,
        "minLength": 1
      },
      "subcategorias": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "nombre",
            "slug"
          ],
          "additionalProperties": false,
          "properties": {
            "nombre": {
              "bsonType": "string",
              "maxLength": 60,
              "minLength": 1
            },
            "slug": {
              "bsonType": "string",
              "maxLength": 60,
              "minLength": 1
            },
            "descripcion": {
              "bsonType": [
                "string",
                "null"
              ],
              "maxLength": 300
            }
          }
        }
      },
      "sinonimos": {
        "bsonType": "array",
        "items": {
          "bsonType": "string"
        }
      },
      "totalPublicaciones": {
        "bsonType": [
          "int",
          "long"
        ],
        "minimum": 0,
        "maximum": 2147483647
      }
    }
  },
  "recomendaciones": {
    "bsonType": "object",
    "required": [
      "_id",
      "usuario",
      "publicacion",
      "criterio",
      "puntuacion",
      "fechaGeneracion",
      "vista",
      "factores"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "usuario": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "publicacion": {
        "bsonType": "object",
        "required": [
          "tipo",
          "archivoUrl"
        ],
        "additionalProperties": false,
        "properties": {
          "titulo": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 150
          },
          "tipo": {
            "bsonType": "string",
            "maxLength": 10,
            "minLength": 1
          },
          "archivoUrl": {
            "bsonType": "string",
            "maxLength": 500,
            "minLength": 1
          }
        }
      },
      "criterio": {
        "bsonType": "string",
        "maxLength": 15,
        "minLength": 1,
        "enum": [
          "etiquetas",
          "coleccion",
          "tendencia",
          "similitud",
          "preferencias"
        ]
      },
      "puntuacion": {
        "bsonType": [
          "double",
          "int",
          "long"
        ],
        "minimum": 0,
        "maximum": 1
      },
      "fechaGeneracion": {
        "bsonType": "date"
      },
      "vista": {
        "bsonType": "bool"
      },
      "factores": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "nombre",
            "peso"
          ],
          "additionalProperties": false,
          "properties": {
            "nombre": {
              "bsonType": "string",
              "maxLength": 60,
              "minLength": 1
            },
            "peso": {
              "bsonType": [
                "double",
                "int",
                "long"
              ],
              "minimum": 0,
              "maximum": 1
            }
          }
        }
      }
    }
  },
  "mensajes": {
    "bsonType": "object",
    "required": [
      "_id",
      "emisor",
      "receptor",
      "tipo",
      "adjuntos",
      "reacciones",
      "leido",
      "eliminadoPor",
      "fechaEnvio"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "emisor": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "receptor": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "contenido": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 5000
      },
      "tipo": {
        "bsonType": "string",
        "maxLength": 10,
        "minLength": 1,
        "enum": [
          "texto",
          "imagen",
          "video",
          "archivo"
        ]
      },
      "adjuntos": {
        "bsonType": "array",
        "items": {
          "bsonType": "string",
          "pattern": "^https?://",
          "maxLength": 500
        },
        "maxItems": 10
      },
      "reacciones": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "usuario",
            "tipoReaccion",
            "fecha"
          ],
          "additionalProperties": false,
          "properties": {
            "usuario": {
              "bsonType": "object",
              "required": [
                "nombreUsuario"
              ],
              "additionalProperties": false,
              "properties": {
                "nombreUsuario": {
                  "bsonType": "string",
                  "maxLength": 30,
                  "minLength": 1
                },
                "imagenPerfil": {
                  "bsonType": [
                    "string",
                    "null"
                  ],
                  "maxLength": 500
                }
              }
            },
            "tipoReaccion": {
              "bsonType": "string",
              "maxLength": 10,
              "minLength": 1,
              "enum": [
                "meGusta",
                "amor",
                "aplauso",
                "sorpresa",
                "triste",
                "risa"
              ]
            },
            "fecha": {
              "bsonType": "date"
            }
          }
        }
      },
      "leido": {
        "bsonType": "bool"
      },
      "fechaLectura": {
        "bsonType": [
          "date",
          "null"
        ]
      },
      "eliminadoPor": {
        "bsonType": "array",
        "items": {
          "bsonType": "string"
        }
      },
      "fechaEnvio": {
        "bsonType": "date"
      }
    }
  },
  "grupos": {
    "bsonType": "object",
    "required": [
      "_id",
      "nombre",
      "tipo",
      "creador",
      "categoria",
      "miembros",
      "foros",
      "reglas",
      "estado",
      "totalMiembros",
      "fechaCreacion"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "nombre": {
        "bsonType": "string",
        "maxLength": 80,
        "minLength": 1
      },
      "descripcion": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 1000
      },
      "tipo": {
        "bsonType": "string",
        "maxLength": 10,
        "minLength": 1,
        "enum": [
          "publico",
          "privado"
        ]
      },
      "imagenUrl": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 500
      },
      "creador": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "categoria": {
        "bsonType": "object",
        "required": [
          "nombre",
          "slug"
        ],
        "additionalProperties": false,
        "properties": {
          "nombre": {
            "bsonType": "string",
            "maxLength": 60,
            "minLength": 1
          },
          "slug": {
            "bsonType": "string",
            "maxLength": 60,
            "minLength": 1
          }
        }
      },
      "miembros": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "nombreUsuario",
            "rol",
            "fechaIngreso"
          ],
          "additionalProperties": false,
          "properties": {
            "nombreUsuario": {
              "bsonType": "string",
              "maxLength": 30,
              "minLength": 1
            },
            "imagenPerfil": {
              "bsonType": [
                "string",
                "null"
              ],
              "maxLength": 500
            },
            "rol": {
              "bsonType": "string",
              "maxLength": 15,
              "minLength": 1,
              "enum": [
                "miembro",
                "moderador",
                "administrador"
              ]
            },
            "fechaIngreso": {
              "bsonType": "date"
            }
          }
        },
        "maxItems": 1000
      },
      "foros": {
        "bsonType": "array",
        "items": {
          "bsonType": "object",
          "required": [
            "nombre",
            "comentarios",
            "fechaCreacion"
          ],
          "additionalProperties": false,
          "properties": {
            "nombre": {
              "bsonType": "string",
              "maxLength": 80,
              "minLength": 1
            },
            "descripcion": {
              "bsonType": [
                "string",
                "null"
              ],
              "maxLength": 500
            },
            "comentarios": {
              "bsonType": "array",
              "items": {
                "bsonType": "object",
                "required": [
                  "autor",
                  "contenido",
                  "formato",
                  "menciones",
                  "archivosAdjuntos",
                  "respuestas",
                  "reacciones",
                  "conteoReacciones",
                  "fijado",
                  "cerrado",
                  "estado",
                  "fechaCreacion"
                ],
                "additionalProperties": false,
                "properties": {
                  "autor": {
                    "bsonType": "object",
                    "required": [
                      "nombreUsuario"
                    ],
                    "additionalProperties": false,
                    "properties": {
                      "nombreUsuario": {
                        "bsonType": "string",
                        "maxLength": 30,
                        "minLength": 1
                      },
                      "imagenPerfil": {
                        "bsonType": [
                          "string",
                          "null"
                        ],
                        "maxLength": 500
                      }
                    }
                  },
                  "titulo": {
                    "bsonType": [
                      "string",
                      "null"
                    ],
                    "maxLength": 150
                  },
                  "contenido": {
                    "bsonType": "string",
                    "maxLength": 1000,
                    "minLength": 1
                  },
                  "formato": {
                    "bsonType": "string",
                    "maxLength": 10,
                    "minLength": 1
                  },
                  "menciones": {
                    "bsonType": "array",
                    "items": {
                      "bsonType": "string"
                    }
                  },
                  "archivosAdjuntos": {
                    "bsonType": "array",
                    "items": {
                      "bsonType": "string"
                    }
                  },
                  "respuestas": {
                    "bsonType": "array",
                    "items": {
                      "bsonType": "object",
                      "required": [
                        "autor",
                        "contenido",
                        "fechaCreacion"
                      ],
                      "additionalProperties": false,
                      "properties": {
                        "autor": {
                          "bsonType": "object",
                          "required": [
                            "nombreUsuario"
                          ],
                          "additionalProperties": false,
                          "properties": {
                            "nombreUsuario": {
                              "bsonType": "string",
                              "maxLength": 30,
                              "minLength": 1
                            },
                            "imagenPerfil": {
                              "bsonType": [
                                "string",
                                "null"
                              ],
                              "maxLength": 500
                            }
                          }
                        },
                        "contenido": {
                          "bsonType": "string",
                          "maxLength": 1000,
                          "minLength": 1
                        },
                        "fechaCreacion": {
                          "bsonType": "date"
                        }
                      }
                    }
                  },
                  "reacciones": {
                    "bsonType": "array",
                    "items": {
                      "bsonType": "object",
                      "required": [
                        "usuario",
                        "tipoReaccion",
                        "fecha"
                      ],
                      "additionalProperties": false,
                      "properties": {
                        "usuario": {
                          "bsonType": "object",
                          "required": [
                            "nombreUsuario"
                          ],
                          "additionalProperties": false,
                          "properties": {
                            "nombreUsuario": {
                              "bsonType": "string",
                              "maxLength": 30,
                              "minLength": 1
                            },
                            "imagenPerfil": {
                              "bsonType": [
                                "string",
                                "null"
                              ],
                              "maxLength": 500
                            }
                          }
                        },
                        "tipoReaccion": {
                          "bsonType": "string",
                          "maxLength": 10,
                          "minLength": 1
                        },
                        "fecha": {
                          "bsonType": "date"
                        }
                      }
                    }
                  },
                  "conteoReacciones": {
                    "bsonType": "object",
                    "required": [
                      "meGusta",
                      "amor",
                      "aplauso",
                      "sorpresa",
                      "triste",
                      "risa"
                    ],
                    "additionalProperties": false,
                    "properties": {
                      "meGusta": {
                        "bsonType": [
                          "int",
                          "long"
                        ],
                        "minimum": 0,
                        "maximum": 2147483647
                      },
                      "amor": {
                        "bsonType": [
                          "int",
                          "long"
                        ],
                        "minimum": 0,
                        "maximum": 2147483647
                      },
                      "aplauso": {
                        "bsonType": [
                          "int",
                          "long"
                        ],
                        "minimum": 0,
                        "maximum": 2147483647
                      },
                      "sorpresa": {
                        "bsonType": [
                          "int",
                          "long"
                        ],
                        "minimum": 0,
                        "maximum": 2147483647
                      },
                      "triste": {
                        "bsonType": [
                          "int",
                          "long"
                        ],
                        "minimum": 0,
                        "maximum": 2147483647
                      },
                      "risa": {
                        "bsonType": [
                          "int",
                          "long"
                        ],
                        "minimum": 0,
                        "maximum": 2147483647
                      }
                    }
                  },
                  "fijado": {
                    "bsonType": "bool"
                  },
                  "cerrado": {
                    "bsonType": "bool"
                  },
                  "estado": {
                    "bsonType": "string",
                    "maxLength": 10,
                    "minLength": 1
                  },
                  "fechaCreacion": {
                    "bsonType": "date"
                  },
                  "fechaEdicion": {
                    "bsonType": [
                      "date",
                      "null"
                    ]
                  }
                }
              },
              "maxItems": 200
            },
            "fechaCreacion": {
              "bsonType": "date"
            }
          }
        },
        "maxItems": 10
      },
      "reglas": {
        "bsonType": "array",
        "items": {
          "bsonType": "string",
          "maxLength": 300
        },
        "maxItems": 20
      },
      "estado": {
        "bsonType": "string",
        "maxLength": 10,
        "minLength": 1,
        "enum": [
          "activo",
          "archivado",
          "suspendido"
        ]
      },
      "totalMiembros": {
        "bsonType": [
          "int",
          "long"
        ],
        "minimum": 0,
        "maximum": 2147483647
      },
      "fechaCreacion": {
        "bsonType": "date"
      }
    }
  },
  "moderacion": {
    "bsonType": "object",
    "required": [
      "_id",
      "tipo",
      "bloqueador",
      "bloqueado",
      "ambito",
      "fechaCreacion"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "tipo": {
        "bsonType": "string",
        "maxLength": 10,
        "minLength": 1,
        "enum": [
          "bloqueo"
        ]
      },
      "bloqueador": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "bloqueado": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "ambito": {
        "bsonType": "string",
        "maxLength": 10,
        "minLength": 1,
        "enum": [
          "total",
          "mensajes",
          "contenido"
        ]
      },
      "fechaExpiracion": {
        "bsonType": [
          "date",
          "null"
        ]
      },
      "fechaCreacion": {
        "bsonType": "date"
      }
    }
  },
  "exploracion": {
    "bsonType": "object",
    "required": [
      "_id",
      "usuario",
      "preferencias",
      "fechaActualizacion"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "usuario": {
        "bsonType": "object",
        "required": [
          "nombreUsuario"
        ],
        "additionalProperties": false,
        "properties": {
          "nombreUsuario": {
            "bsonType": "string",
            "maxLength": 30,
            "minLength": 1
          },
          "imagenPerfil": {
            "bsonType": [
              "string",
              "null"
            ],
            "maxLength": 500
          }
        }
      },
      "preferencias": {
        "bsonType": "object",
        "required": [
          "categorias",
          "etiquetas",
          "artistas"
        ],
        "additionalProperties": false,
        "properties": {
          "categorias": {
            "bsonType": "array",
            "items": {
              "bsonType": "string"
            }
          },
          "etiquetas": {
            "bsonType": "array",
            "items": {
              "bsonType": "string"
            }
          },
          "artistas": {
            "bsonType": "array",
            "items": {
              "bsonType": "string"
            }
          }
        }
      },
      "fechaActualizacion": {
        "bsonType": "date"
      }
    }
  },
  "roles": {
    "bsonType": "object",
    "required": [
      "_id",
      "nombre",
      "descripcion",
      "permiso_usuarios",
      "permiso_contenido",
      "permiso_estadisticas",
      "activo"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "nombre": {
        "bsonType": "string",
        "maxLength": 50,
        "minLength": 1
      },
      "descripcion": {
        "bsonType": "string",
        "minLength": 1
      },
      "permiso_usuarios": {
        "bsonType": "bool"
      },
      "permiso_contenido": {
        "bsonType": "bool"
      },
      "permiso_estadisticas": {
        "bsonType": "bool"
      },
      "activo": {
        "bsonType": "bool"
      }
    }
  },
  "accionesAdministrativas": {
    "bsonType": "object",
    "required": [
      "_id",
      "administrador",
      "rol_administrador",
      "accion",
      "entidad",
      "detalle_entidad",
      "descripcion",
      "fecha"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "administrador": {
        "bsonType": "string",
        "maxLength": 100,
        "minLength": 1
      },
      "rol_administrador": {
        "bsonType": "string",
        "maxLength": 50,
        "minLength": 1
      },
      "accion": {
        "bsonType": "string",
        "maxLength": 100,
        "minLength": 1
      },
      "entidad": {
        "bsonType": "string",
        "maxLength": 50,
        "minLength": 1
      },
      "detalle_entidad": {
        "bsonType": "string",
        "minLength": 1
      },
      "descripcion": {
        "bsonType": "string",
        "minLength": 1
      },
      "fecha": {
        "bsonType": "date"
      }
    }
  },
  "reporteContenido": {
    "bsonType": "object",
    "required": [
      "_id",
      "contenido",
      "tipo_contenido",
      "motivo",
      "estado",
      "reportado_por",
      "fecha_reporte"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "contenido": {
        "bsonType": "string",
        "maxLength": 500,
        "minLength": 1
      },
      "tipo_contenido": {
        "bsonType": "string",
        "maxLength": 50,
        "minLength": 1,
        "enum": [
          "publicacion",
          "comentario",
          "usuario"
        ]
      },
      "motivo": {
        "bsonType": "string",
        "minLength": 1,
        "maxLength": 1000
      },
      "estado": {
        "bsonType": "string",
        "maxLength": 50,
        "minLength": 1,
        "enum": [
          "pendiente",
          "resuelto",
          "descartado"
        ]
      },
      "reportado_por": {
        "bsonType": "string",
        "maxLength": 100,
        "minLength": 1
      },
      "fecha_reporte": {
        "bsonType": "date"
      },
      "moderador": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 100
      },
      "accion_tomada": {
        "bsonType": [
          "string",
          "null"
        ],
        "maxLength": 100
      },
      "fecha_resolucion": {
        "bsonType": [
          "date",
          "null"
        ]
      }
    },
    "oneOf": [
      {
        "properties": {
          "estado": {
            "enum": [
              "pendiente"
            ]
          },
          "moderador": {
            "bsonType": "null"
          },
          "accion_tomada": {
            "bsonType": "null"
          },
          "fecha_resolucion": {
            "bsonType": "null"
          }
        }
      },
      {
        "required": [
          "moderador",
          "accion_tomada",
          "fecha_resolucion"
        ],
        "properties": {
          "estado": {
            "enum": [
              "resuelto",
              "descartado"
            ]
          },
          "moderador": {
            "bsonType": "string"
          },
          "accion_tomada": {
            "bsonType": "string"
          },
          "fecha_resolucion": {
            "bsonType": "date"
          }
        }
      }
    ]
  },
  "controlSistema": {
    "bsonType": "object",
    "required": [
      "_id",
      "fecha",
      "usuarios_activos",
      "publicaciones",
      "reportes",
      "estado_respaldo"
    ],
    "additionalProperties": false,
    "properties": {
      "_id": {
        "bsonType": "objectId"
      },
      "fecha": {
        "bsonType": "date"
      },
      "usuarios_activos": {
        "bsonType": [
          "int",
          "long"
        ],
        "minimum": 0,
        "maximum": 2147483647
      },
      "publicaciones": {
        "bsonType": [
          "int",
          "long"
        ],
        "minimum": 0,
        "maximum": 2147483647
      },
      "reportes": {
        "bsonType": [
          "int",
          "long"
        ],
        "minimum": 0,
        "maximum": 2147483647
      },
      "fecha_respaldo": {
        "bsonType": [
          "date",
          "null"
        ]
      },
      "estado_respaldo": {
        "bsonType": "string",
        "maxLength": 30,
        "minLength": 1
      }
    }
  }
};
var indices = {
  "usuarios": [
    [
      "nombreUsuario"
    ],
    [
      "correo"
    ]
  ],
  "publicaciones": [
    [
      "archivoUrl"
    ]
  ],
  "categorias": [
    [
      "nombre"
    ],
    [
      "slug"
    ]
  ],
  "grupos": [
    [
      "nombre"
    ]
  ],
  "roles": [
    [
      "nombre"
    ]
  ],
  "exploracion": [
    [
      "usuario.nombreUsuario"
    ]
  ],
  "recomendaciones": [
    [
      "usuario.nombreUsuario",
      "publicacion.archivoUrl",
      "criterio"
    ]
  ]
};
var existentes = base.getCollectionNames();
Object.keys(esquemas).forEach(function (nombre) {
    if (existentes.includes(nombre)) {
        var incompatible = base.getCollection(nombre).findOne({ $nor: [{ $jsonSchema: esquemas[nombre] }] });
        if (incompatible) {
            throw new Error("Documento incompatible en " + nombre + ": " + incompatible._id + ". No se aplicaron los esquemas.");
        }
    }
    (indices[nombre] || []).forEach(function (campos) {
        var clave = {};
        campos.forEach(function (campo) { clave[campo.replace(/\./g, "_")] = "$" + campo; });
        var duplicados = base.getCollection(nombre).aggregate([{ $group: { _id: clave, cantidad: { $sum: 1 } } }, { $match: { cantidad: { $gt: 1 } } }, { $limit: 1 }]).toArray();
        if (duplicados.length) throw new Error("Hay valores duplicados en " + nombre + ": " + campos.join(", "));
    });
});
Object.keys(esquemas).forEach(function (nombre) {
    var validacion = { validator: { $jsonSchema: esquemas[nombre] }, validationLevel: "strict", validationAction: "error" };
    if (existentes.includes(nombre)) {
        var resultado = base.runCommand(Object.assign({ collMod: nombre }, validacion));
        if (resultado.ok !== 1) throw new Error("No se pudo validar " + nombre + ": " + resultado.errmsg);
    } else {
        base.createCollection(nombre, validacion);
    }
    (indices[nombre] || []).forEach(function (campos) {
        var clave = {};
        campos.forEach(function (campo) { clave[campo] = 1; });
        base.getCollection(nombre).createIndex(clave, { unique: true });
    });
});
print("Colecciones e índices preparados.");
